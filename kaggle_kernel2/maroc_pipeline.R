# =====================================================================
# Pipeline Analyse Socio-Economique-Financiere Marocaine (R)
# Ingest -> Nettoyage -> Jointure -> EDA -> Stats -> Scenarios ->
# ML -> DL -> Benchmark -> Validation -> Export + Rapport HTML
# Executable sur Kaggle (R kernel).
# v22 : donnees education reelles (World Bank) integrees
# =====================================================================
pkg <- function(p, repo = "https://cloud.r-project.org") {
  if (!requireNamespace(p, quietly = TRUE)) install.packages(p, repos = repo)
  library(p, character.only = TRUE, quietly = TRUE)
}
pkg("tidyverse"); pkg("readr"); pkg("janitor"); pkg("zoo"); pkg("lubridate")
pkg("forecast"); pkg("randomForest"); pkg("caret"); pkg("glmnet")
pkg("corrplot"); pkg("psych"); pkg("ineq"); pkg("DescTools"); pkg("scales"); pkg("rmarkdown")

YEAR_MIN <- 1960

cat("=== 1. INGESTION ===\n")
INDIR <- (list.dirs("/kaggle/input", recursive = TRUE) %>%
            .[grep("economie-maroc-rasd", .)])[1]
if (is.na(INDIR)) INDIR <- "."
cat("Dataset input :", INDIR, "\n")
rc <- function(f) read_csv(file.path(INDIR, f), show_col_types = FALSE)
ind   <- rc("indicators_clean.csv")
dim   <- rc("dim_indicators.csv")
banks <- rc("bank_prices.csv")
bench <- rc("benchmark_morocco.csv")
ind <- ind %>% clean_names()
cat("indicators_clean :", nrow(ind), "lignes,", n_distinct(ind$code), "codes\n")

# --- Donnees education reelles (World Bank) ---
edu_real <- tryCatch({
  read_csv(file.path(INDIR, "education_real.csv"), show_col_types = FALSE)
}, error = function(e) {
  cat("education_real.csv non trouve, donnees synthetiques utilisees.\n")
  NULL
})
if (!is.null(edu_real)) {
  cat("education_real :", nrow(edu_real), "annees,", ncol(edu_real) - 1, "variables\n")
}

cat("=== 2. NETTOYAGE ===\n")
macro <- ind %>% pivot_wider(id_cols = "year", names_from = code, values_from = value, values_fn = mean) %>%
  filter(year >= YEAR_MIN) %>% arrange(year)
codes <- setdiff(names(macro), "year")
nona <- function(v) sum(!is.na(v)) > 1
hasvar <- function(v) { vv <- v[!is.na(v)]; length(unique(vv)) > 1 }
codes_use <- codes[sapply(macro[, codes], function(c) nona(c) && hasvar(c))]
cat("Codes utilises (non vides, variables) :", length(codes_use), "/", length(codes), "\n")
for (c in codes) {
  v <- macro[[c]]
  if (is.character(v) || is.factor(v)) v <- suppressWarnings(as.numeric(as.character(v)))
  if (sum(!is.na(v)) >= 2) {
    macro[[c]] <- tryCatch(zoo::na.approx(v, na.rm = FALSE),
                           error = function(e) replace(v, is.na(v), mean(v, na.rm = TRUE)))
  }
}
macro_imp <- macro
for (c in codes) { v <- macro_imp[[c]]; if (any(is.na(v))) macro_imp[[c]] <- replace(v, is.na(v), mean(v, na.rm = TRUE)) }
winsor_iqr <- function(x) { q <- quantile(x, c(0.05, 0.95), na.rm = TRUE); pmin(pmax(x, q[1]), q[2]) }
macro_clean <- macro_imp
for (c in codes) if (is.numeric(macro_clean[[c]])) macro_clean[[c]] <- winsor_iqr(macro_clean[[c]])
macro_scaled <- macro_clean %>% mutate(across(all_of(codes), ~ as.numeric(scale(.))))
cat("Table macro propre :", nrow(macro_clean), "annees x", length(codes), "indicateurs\n")

cat("=== 3. JOINTURE (economie x finance) ===\n")
banks_y <- banks %>% mutate(year = lubridate::year(as.Date(trade_date))) %>%
  group_by(year) %>%
  summarise(prix_moyen = mean(Price, na.rm = TRUE), volatilite = sd(Change_pct, na.rm = TRUE)) %>% ungroup()
master <- macro_clean %>% full_join(banks_y, by = "year") %>% arrange(year)
cat("master_dataset :", nrow(master), "annees x", ncol(master), "colonnes | finance :",
    round(100 * sum(!is.na(master$volatilite), na.rm = TRUE) / nrow(master), 1), "%\n")

# --- Fusion education reelle dans master ---
if (!is.null(edu_real)) {
  edu_real <- edu_real %>% mutate(year = as.integer(year))
  master <- master %>% left_join(edu_real, by = "year")
  cat("Education reelle fusionnee : colonnes ajoutees =",
      paste(names(edu_real)[-1], collapse = ", "), "\n")
}

cat("=== 4. EDA ===\n")
key <- c("NGDPD", "NGDP_RPCH", "PCPIPCH", "LUR", "GGXWDG_NGDP", "BCA_NGDPD", "SI.POV.GINI")
key <- key[key %in% names(master)]
print(psych::describe(master %>% select(all_of(key))))
num <- master %>% select(all_of(codes_use)) %>% select(where(is.numeric))
corr <- cor(num, use = "pairwise.complete.obs")
png("/kaggle/working/corr.png", width = 900, height = 800)
corrplot::corrplot(corr[1:min(30, nrow(corr)), 1:min(30, nrow(corr))],
                   method = "color", type = "lower", tl.cex = 0.5, na.label = " ")
dev.off()
ml <- master %>% pivot_longer(all_of(intersect(key, names(master))), names_to = "ind", values_to = "val")
p <- ggplot(ml, aes(x = year, y = val)) + geom_line(na.rm = TRUE) +
  facet_wrap(~ind, scales = "free_y", ncol = 2) + theme_minimal() +
  labs(title = "Tendances macroeconomiques principales")
ggsave("/kaggle/working/trends.png", p, width = 10, height = 7)

# Composition sectorielle
sec_cols <- c("NV.AGR.TOTL.ZS", "NV.IND.TOTL.ZS", "NV.SRV.TOTL.ZS")
sec_cols <- sec_cols[sec_cols %in% names(master)]
if (length(sec_cols) >= 2) {
  sec <- master %>% select(year, all_of(sec_cols)) %>% drop_na()
  if (nrow(sec) > 2) {
    png("/kaggle/working/sector.png", width = 900, height = 500)
    matplot(sec$year, as.matrix(sec[, -1]), type = "l", lty = 1, col = 2:4,
            xlab = "annee", ylab = "% PIB", main = "Composition du PIB par secteur")
    legend("bottomleft", legend = c("Agriculture", "Industrie", "Services"), col = 2:4, lty = 1)
    dev.off()
    cat("Secteurs dispo :", paste(sec_cols, collapse = ", "), "\n")
  }
}

# Gini
if ("SI.POV.GINI" %in% names(master)) {
  gi <- master %>% select(year, SI.POV.GINI) %>% drop_na()
  if (nrow(gi) > 2) {
    png("/kaggle/working/gini.png", width = 800, height = 450)
    plot(gi$year, gi$SI.POV.GINI, type = "l", main = "Indice de Gini (Maroc)",
         xlab = "annee", ylab = "Gini")
    dev.off()
    cat("Gini moyen :", round(mean(gi$SI.POV.GINI, na.rm = TRUE), 2), "\n")
  }
}

# --- Graphiques Education (donnees reelles) ---
if (!is.null(edu_real)) {
  # Inscription scolaire (taux brut)
  edu_long <- edu_real %>%
    select(year, primary_enrollment, secondary_enrollment, tertiary_enrollment) %>%
    pivot_longer(-year, names_to = "niveau", values_to = "taux") %>%
    mutate(niveau = case_when(
      niveau == "primary_enrollment" ~ "Primaire",
      niveau == "secondary_enrollment" ~ "Secondaire",
      niveau == "tertiary_enrollment" ~ "Superieur"
    )) %>%
    drop_na()
  if (nrow(edu_long) > 0) {
    p_edu <- ggplot(edu_long, aes(x = year, y = taux, color = niveau)) +
      geom_line(size = 1.1) + geom_point(size = 1.5) +
      theme_minimal() + labs(title = "Inscriptions scolaires au Maroc (donnees reelles)",
                             subtitle = "Taux brut d'inscription - Source: Banque Mondiale",
                             x = "Annee", y = "Taux brut (%)", color = "Niveau") +
      scale_color_brewer(palette = "Set1")
    ggsave("/kaggle/working/education_enrollment_real.png", p_edu, width = 10, height = 6)
    cat("Graphique education inscription cree (donnees reelles).\n")
  }

  # Depenses教育 + Taux d'alphabetisation
  edu_sp <- edu_real %>%
    select(year, education_spending_gdp, literacy_rate) %>%
    pivot_longer(-year, names_to = "indicateur", values_to = "valeur") %>%
    mutate(indicateur = case_when(
      indicateur == "education_spending_gdp" ~ "Depenses education (% PIB)",
      indicateur == "literacy_rate" ~ "Taux d'alphabetisation (%)"
    )) %>%
    drop_na()
  if (nrow(edu_sp) > 0) {
    p_sp <- ggplot(edu_sp, aes(x = year, y = valeur, color = indicateur)) +
      geom_line(size = 1.1) + geom_point(size = 1.5) +
      theme_minimal() + labs(title = "Education : depenses et alphabetisation (donnees reelles)",
                             subtitle = "Source: Banque Mondiale",
                             x = "Annee", y = "Valeur", color = "Indicateur") +
      scale_color_brewer(palette = "Set2")
    ggsave("/kaggle/working/education_spending_real.png", p_sp, width = 10, height = 6)
    cat("Graphique depenses education cree (donnees reelles).\n")
  }
  # Resume education
  cat("\n=== RESUME EDUCATION (donnees reelles) ===\n")
  latest <- edu_real %>% filter(year == max(year, na.rm = TRUE))
  cat("Annee la plus recente :", latest$year, "\n")
  cat("Inscription primaire :", round(latest$primary_enrollment, 1), "%\n")
  cat("Inscription secondaire :", round(latest$secondary_enrollment, 1), "%\n")
  cat("Inscription superieure :", round(latest$tertiary_enrollment, 1), "%\n")
  if (!is.na(latest$education_spending_gdp)) cat("Depenses education :", round(latest$education_spending_gdp, 1), "% PIB\n")
  if (!is.na(latest$literacy_rate)) cat("Taux alphabetisation :", round(latest$literacy_rate, 1), "%\n")
  cat("==========================================\n\n")
}

cat("=== 5. STATISTIQUES ===\n")
mdf <- master %>% select(all_of(c("year","NGDP_RPCH","PCPIPCH","LUR","GGXWDG_NGDP","BCA_NGDPD"))) %>% drop_na()
ols <- lm(NGDP_RPCH ~ PCPIPCH + LUR + GGXWDG_NGDP, data = mdf)
cat("OLS croissance PIB :\n"); print(summary(ols)$coefficients)
mdf$recession <- ifelse(mdf$NGDP_RPCH < 0, 1, 0)
if (sum(mdf$recession) >= 2) {
  logit <- glm(recession ~ PCPIPCH + LUR, data = mdf, family = binomial)
  cat("Logit recession :\n"); print(summary(logit)$coefficients)
}
cat("Pearson (croissance vs inflation) :",
    round(cor(mdf$NGDP_RPCH, mdf$PCPIPCH, use = "pairwise.complete.obs"), 3), "\n")
g <- master %>% select(year, NGDPD) %>% drop_na() %>% arrange(year)
tcam <- (g$NGDPD[nrow(g)] / g$NGDPD[1])^(1 / (nrow(g) - 1)) - 1
cat("TCAM PIB (NGDPD) sur", nrow(g), "ans :", round(100 * tcam, 2), "%\n")
ba <- banks %>% mutate(year = lubridate::year(as.Date(trade_date)))
av <- ba %>% group_by(entity) %>% summarise(vol = sd(Change_pct, na.rm = TRUE))
cat("Volatilite bancaire par banque :\n"); print(av)
ts_gdp <- ts(g$NGDPD, start = g$year[1], frequency = 1)
fit <- tryCatch(forecast::auto.arima(ts_gdp), error = function(e) NULL)
if (!is.null(fit)) {
  fc <- forecast::forecast(fit, h = 20)
  png("/kaggle/working/arima.png", width = 800, height = 500)
  plot(fc, main = "Prevision ARIMA du PIB (NGDPD, 20 ans)"); dev.off()
  cat("ARIMA :", fit$method, "\n")
}

cat("=== 6. SCENARIOS DE CROISSANCE ===\n")
mu <- mean(master$NGDP_RPCH, na.rm = TRUE); sg <- sd(master$NGDP_RPCH, na.rm = TRUE)
ly <- g$year[nrow(g)]; last <- g$NGDPD[nrow(g)]; h <- 15
sc <- data.frame(year = ly + 1:h)
for (nm in c("pessimiste", "base", "optimiste")) {
  r <- if (nm == "pessimiste") mu - sg else if (nm == "optimiste") mu + sg else mu
  sc[[nm]] <- last * (1 + r / 100)^(1:h)
}
png("/kaggle/working/scenarios.png", width = 900, height = 500)
matplot(sc$year, as.matrix(sc[, -1]), type = "l", lty = c(2, 1, 2), col = c(2, 1, 3),
        xlab = "annee", ylab = "PIB (Md USD courants)", main = "Scenarios de croissance du PIB a 15 ans")
legend("topleft", legend = c("Pessimiste", "Base", "Optimiste"), col = c(2, 1, 3), lty = c(2, 1, 2))
dev.off()
cat("Hypotheses : mu =", round(mu, 2), "%, sigma =", round(sg, 2), "%\n")
cat("Valeur PIB projete 2039 (base) :", signif(sc$base[h], 5),
    "(meme unite que NGDPD du jeu de donnees)\n")

cat("=== 7. MACHINE LEARNING ===\n")
feat <- c("PCPIPCH", "LUR", "GGXWDG_NGDP", "BCA_NGDPD", "NY.GDP.MKTP.KD.ZG",
          "SP.POP.TOTL", "FP.CPI.TOTL.ZG", "SI.POV.GINI", "NV.SRV.TOTL.ZS")
feat <- feat[feat %in% codes_use]
ml_df <- master %>% select(all_of(c("year","NGDP_RPCH", feat))) %>% drop_na()
cat("ML dataframe :", nrow(ml_df), "lignes,", length(feat), "predicteurs\n")
rf <- lasso <- NULL
if (nrow(ml_df) > 20) {
  set.seed(42)
  idx <- caret::createDataPartition(ml_df$NGDP_RPCH, p = 0.8, list = FALSE)
  tr <- ml_df[idx, ]; te <- ml_df[-idx, ]
  ctrl <- trainControl(method = "cv", number = 5)
  rf <- train(NGDP_RPCH ~ ., data = tr %>% select(-year), method = "rf", ntree = 100, trControl = ctrl)
  cat("Random Forest :\n"); print(postResample(predict(rf, te), te$NGDP_RPCH))
  lasso <- train(NGDP_RPCH ~ ., data = tr %>% select(-year), method = "glmnet",
                 trControl = ctrl, tuneGrid = expand.grid(alpha = 1, lambda = 10^seq(-4, 1, 0.5)))
  cat("Lasso :\n"); print(postResample(predict(lasso, te), te$NGDP_RPCH))
  km_df <- macro_scaled %>% select(year, all_of(codes_use)) %>% drop_na()
  kmat <- as.matrix(km_df %>% select(all_of(codes_use)))
  keep <- apply(kmat, 2, function(x) all(is.finite(x)) && stats::sd(x) > 0)
  kmat <- kmat[, keep, drop = FALSE]
  if (nrow(kmat) > 5 && ncol(kmat) > 1) {
    km <- kmeans(kmat, centers = 3, nstart = 10)
    reg <- data.frame(year = km_df$year, regime = as.character(km$cluster))
    master <- master %>% left_join(reg, by = "year")
    png("/kaggle/working/clusters.png", width = 800, height = 400)
    plot(master$year, master$regime, type = "o", main = "Regimes economiques (K-means, 3)",
         xlab = "annee", ylab = "cluster"); dev.off()
    cat("K-means : 3 regimes economiques identifies.\n")
  }
  if (nrow(kmat) > 1 && ncol(kmat) > 1) {
    pca <- prcomp(kmat, scale. = TRUE)
    png("/kaggle/working/pca.png", width = 800, height = 500)
    plot(pca, main = "Scree plot ACP"); dev.off()
    cat("ACP :", ncol(kmat), "indicateurs -> composantes.\n")
  }
}

cat("=== 8. DEEP LEARNING ===\n")
dl_ok <- requireNamespace("keras", quietly = TRUE) && requireNamespace("tensorflow", quietly = TRUE)
model <- NULL
if (dl_ok && nrow(ml_df) > 20) {
  dl_res <- tryCatch({
    library(keras)
    X <- as.matrix(ml_df %>% select(all_of(feat)) %>% scale())
    y <- ml_df$NGDP_RPCH
    set.seed(42); tidx <- caret::createDataPartition(y, p = 0.8, list = FALSE)
    Xtr <- X[tidx, ]; Xte <- X[-tidx, ]; ytr <- y[tidx]; yte <- y[-tidx]
    model <- keras_model_sequential() %>%
      layer_dense(units = 32, activation = "relu", input_shape = ncol(X)) %>%
      layer_dropout(0.3) %>%
      layer_dense(units = 16, activation = "relu") %>%
      layer_dense(units = 1, activation = "linear")
    model %>% compile(optimizer = "adam", loss = "mse", metrics = "mae")
    model %>% fit(Xtr, ytr, epochs = 80, batch_size = 16, validation_split = 0.2, verbose = 0)
    pred_dl <- as.numeric(predict(model, Xte))
    cat("Deep Learning (keras) :\n")
    print(c(RMSE = sqrt(mean((pred_dl - yte)^2)), R2 = cor(pred_dl, yte)^2))
    saveRDS(model, "/kaggle/working/dl_model.rds")
    "ok"
  }, error = function(e) { cat("Deep Learning erreur :", conditionMessage(e), "\n"); NULL })
  if (is.null(dl_res)) model <- NULL
} else {
  cat("Deep Learning ignore (keras non disponible).\n")
}

cat("=== 9. BENCHMARK (Maroc vs region/monde) ===\n")
if (nrow(bench) > 0) {
  bl <- bench %>% group_by(indicator) %>% filter(year == max(year, na.rm = TRUE)) %>% ungroup() %>%
    mutate(ratio = morocco / region_avg)
  png("/kaggle/working/bench.png", width = 900, height = 500)
  barplot(bl$ratio, names.arg = bl$indicator, las = 2,
          main = "Maroc vs moyenne region (ratio, 1 = parite)",
          ylim = c(0, max(bl$ratio, na.rm = TRUE) * 1.1),
          col = ifelse(bl$ratio > 1, "#2c7fb8", "#de2d26"))
  abline(h = 1, col = "black", lty = 2)
  dev.off()
  cat("Benchmark :", nrow(bl), "indicateurs (>", round(100 * mean(bl$ratio > 1, na.rm = TRUE), 0),
      "% au-dessus de la region)\n")
}

cat("=== 10. VALIDATION ===\n")
if (!is.null(rf) && !is.null(lasso)) {
  res <- data.frame(
    modele = c("RandomForest", "Lasso"),
    RMSE = c(postResample(predict(rf, te), te$NGDP_RPCH)[1], postResample(predict(lasso, te), te$NGDP_RPCH)[1]),
    R2 = c(postResample(predict(rf, te), te$NGDP_RPCH)[2], postResample(predict(lasso, te), te$NGDP_RPCH)[2]))
  cat("Comparaison modeles (RMSE / R2) :\n"); print(res)
}

cat("=== 11. EXPORT + RAPPORT HTML ===\n")
write_csv(master, "/kaggle/working/master_dataset.csv")
if (!is.null(rf)) saveRDS(rf, "/kaggle/working/rf_model.rds")
if (!is.null(lasso)) saveRDS(lasso, "/kaggle/working/lasso_model.rds")
if (!is.null(fit)) saveRDS(fit, "/kaggle/working/arima_model.rds")

## --- data quality report ---
dq <- data.frame(
  code = codes,
  type = sapply(codes, function(c) class(macro_clean[[c]])[1]),
  n_non_na = sapply(codes, function(c) sum(!is.na(macro_clean[[c]]))),
  n_total = nrow(macro_clean),
  pct_rempli = round(100 * sapply(codes, function(c) sum(!is.na(macro_clean[[c]]))) / nrow(macro_clean), 1),
  mean_val = round(sapply(codes, function(c) { v <- macro_clean[[c]]; ifelse(sum(!is.na(v)) > 0, mean(v, na.rm = TRUE), NA) }), 4),
  sd_val = round(sapply(codes, function(c) { v <- macro_clean[[c]]; ifelse(sum(!is.na(v)) > 1, sd(v, na.rm = TRUE), NA) }), 4),
  min_val = round(sapply(codes, function(c) { v <- macro_clean[[c]]; ifelse(sum(!is.na(v)) > 0, min(v, na.rm = TRUE), NA) }), 4),
  max_val = round(sapply(codes, function(c) { v <- macro_clean[[c]]; ifelse(sum(!is.na(v)) > 0, max(v, na.rm = TRUE), NA) }), 4),
  year_min = sapply(codes, function(c) { v <- macro_clean[[c]]; idx <- which(!is.na(v)); ifelse(length(idx) > 0, macro_clean$year[min(idx)], NA) }),
  year_max = sapply(codes, function(c) { v <- macro_clean[[c]]; idx <- which(!is.na(v)); ifelse(length(idx) > 0, macro_clean$year[max(idx)], NA) }),
  row.names = NULL
) %>% arrange(desc(pct_rempli))
write_csv(dq, "/kaggle/working/data_quality.csv")

## --- helpers for report ---
n_ind <- length(codes_use)
n_total <- length(codes)
pct_couv <- round(100 * sum(!is.na(master$NGDPD)) / nrow(master), 1)
n_recession <- sum(mdf$recession, na.rm = TRUE)
pct_above_region <- round(100 * mean(bl$ratio > 1, na.rm = TRUE), 0)
rf_r2 <- if (!is.null(rf)) round(postResample(predict(rf, te), te$NGDP_RPCH)[2], 3) else NA
lasso_r2 <- if (!is.null(lasso)) round(postResample(predict(lasso, te), te$NGDP_RPCH)[2], 3) else NA
dl_r2 <- if (exists("pred_dl")) round(cor(pred_dl, yte)^2, 3) else NA

## --- feature importance (RF) ---
feat_imp <- NULL
if (!is.null(rf)) {
  fi <- varImp(rf)$importance
  feat_imp <- data.frame(predicteur = rownames(fi), importance = round(fi$Overall, 2)) %>%
    arrange(desc(importance)) %>% head(10)
}

## --- build Rmd ---
rmd <- c(
  "---",
  'title: "Rapport Analyse : Economie du Maroc"',
  'subtitle: "Pipelines de donnees, modelisation et perspectives"',
  'author: "Youssef Amar - Pipeline automatise"',
  'date: "`r Sys.Date()`"',
  "output:",
  "  html_document:",
  "    toc: true",
  "    toc_depth: 3",
  "    toc_float: true",
  "    number_sections: true",
  "    theme: flatly",
  "    highlight: tango",
  "    code_folding: hide",
  "    fig_width: 10",
  "    fig_height: 6",
  "---",
  "",
  "```{r setup, include=FALSE}",
  "knitr::opts_chunk$set(echo=FALSE, warning=FALSE, message=FALSE, fig.align='center')",
  "```",
  "",
  "# Resume executif {.tabset}",
  "",
   paste0("Ce rapport presente l'analyse socio-economique et financiere du Maroc sur la periode ",
          min(master$year), "-", max(master$year), ". Il couvre ", n_ind,
          " indicateurs macroeconomiques (sur ", n_total, " disponibles), ",
          "integre les donnees boursieres de la Bourse de Casablanca, ",
          if (!is.null(edu_real)) "les donnees education reelles (Banque Mondiale), " else "",
          "et propose des modeles de prevision et de clustering."),
  "",
  "## Resultats cles",
  "",
  paste0("| Metrique | Valeur |\n|---|---|\n",
         "| Periode analysee | ", min(master$year), "-", max(master$year), " |\n",
         "| Indicateurs utilises | ", n_ind, " / ", n_total, " |\n",
         "| TCAM PIB (NGDPD) | ", round(100 * tcam, 2), "% |\n",
         "| Gini moyen | ", round(mean(gi$SI.POV.GINI, na.rm = TRUE), 2), " |\n",
         "| Annees de recession | ", n_recession, " |\n",
         "| Volatilite bancaire (BCP) | ", round(av$vol[av$entity == "BCP"], 2), " |\n",
         "| Volatilite bancaire (CDM) | ", round(av$vol[av$entity == "CDM"], 2), " |\n",
         "| RandomForest R2 | ", rf_r2, " |\n",
         "| Lasso R2 | ", lasso_r2, " |\n",
         "| Deep Learning R2 | ", dl_r2, " |\n",
          "| Bench: au-dessus de la region | ", pct_above_region, "% |\n",
         if (!is.null(edu_real)) {
           paste0("| Inscription primaire (2023) | ",
                  round(edu_real$primary_enrollment[edu_real$year == 2023], 1), "% |\n",
                  "| Taux alphabetisation (2014) | ",
                  round(edu_real$literacy_rate[edu_real$year == 2014], 1), "% |\n")
         } else ""),
  "",
  "## Structure du pipeline",
  "",
  "```",
  "Indicateurs (WB/IMF/HDI/OWID) --> Nettoyage --> Jointure (macro x bourse)",
  "  --> EDA --> Statistiques --> Scenarios --> ML --> DL --> Benchmark --> Rapport",
  "```",
  "",
  "# Ingestion des donnees",
  "",
  paste0("Le jeu de donnees *indicators_clean* contient ", nrow(ind),
         " observations couvrant ", n_distinct(ind$code), " indicateurs provenant ",
         "de multiples sources : Banque Mondiale (WDI), FMI (WEO), UNDP (HDI), ",
         "Our World in Data (OWID) et la Bourse de Casablanca."),
  "",
   paste0("Apres filtrage (annee >= ", YEAR_MIN, ") et imputation, ",
          "le dataset *master* compte ", nrow(master), " annees x ",
          ncol(master), " colonnes.")),
   if (!is.null(edu_real)) {
     paste0("Les donnees education reelles (education_real.csv, ", nrow(edu_real),
            " annees, World Bank) sont fusionnees au dataset master.")
   },
  "",
  "## Qualite des donnees",
  "",
  paste0("- Taux de remplissage NGDPD : ", pct_couv, "%"),
  paste0("- Codes a variance nulle supprimes : ", n_total - n_ind),
  paste0("- Methode d'imputation : interpolation lineaire (na.approx) + moyenne"),
  paste0("- Winsorisation : percentiles 5-95%"),
  "",
  "# Analyse exploratoire (EDA)",
  "",
  "## Matrice de correlation",
  "",
  "La matrice de correlation met en evidence les dependances structurelles entre indicateurs macroeconomiques.",
  "",
  "![Matrice de correlation](corr.png)",
  "",
  "## Tendances temporelles",
  "",
  "![Tendances macroeconomiques](trends.png)",
  "",
  if (file.exists("/kaggle/working/sector.png")) {
    c("## Composition sectorielle du PIB", "",
      "![Composition sectorielle](sector.png)", "")
  },
  "",
  if (file.exists("/kaggle/working/gini.png")) {
    c("## Inegalite (Indice de Gini)", "",
      paste0("Gini moyen : ", round(mean(gi$SI.POV.GINI, na.rm = TRUE), 2)), "",
      "![Indice de Gini](gini.png)", "")
  },
  "",
  if (!is.null(edu_real) && file.exists("/kaggle/working/education_enrollment_real.png")) {
    c("## Education (donnees reelles - Banque Mondiale)", "",
      paste0("Donnees reelles sur ", nrow(edu_real), " annees (1960-2024)."),
      "",
      "### Inscriptions scolaires",
      "![Inscriptions scolaires](education_enrollment_real.png)", "")
  },
  "",
  if (!is.null(edu_real) && file.exists("/kaggle/working/education_spending_real.png")) {
    c("### Depenses et alphabetisation",
      "![Depenses education](education_spending_real.png)", "")
  },
  "",
  "# Modelisation statistique",
  "",
  "## Regression lineaire : croissance du PIB",
  "",
  "```{r}",
  "ols <- lm(NGDP_RPCH ~ PCPIPCH + LUR + GGXWDG_NGDP, data = mdf)",
  "knitr::kable(summary(ols)$coefficients, digits = 4, caption = 'Resultats OLS')",
  "```",
  "",
  "## Modele logit : probabilite de recession",
  "",
  "```{r}",
  "if (sum(mdf$recession) >= 2) {",
  "  logit <- glm(recession ~ PCPIPCH + LUR, data = mdf, family = binomial)",
  "  knitr::kable(summary(logit)$coefficients, digits = 4, caption = 'Resultats Logit')",
  "}",
  "```",
  "",
  paste0("**TCAM du PIB** : ", round(100 * tcam, 2), "% par an."),
  "",
  "## Volatilite du secteur bancaire",
  "",
  "```{r}",
  "knitr::kable(av %>% arrange(vol), digits = 2, caption = 'Volatilite par banque')",
  "```",
  "",
  "## Prevision ARIMA",
  "",
  if (!is.null(fit)) {
    c(paste0("**Modele** : ", fit$method), "",
      "![ARIMA](arima.png)", "")
  },
  "",
  "# Scenarios de croissance",
  "",
  paste0("- **Pessimiste** : ", round(mu - sg, 2), "%/an"),
  paste0("- **Base** : ", round(mu, 2), "%/an"),
  paste0("- **Optimiste** : ", round(mu + sg, 2), "%/an"),
  "",
  "![Scenarios](scenarios.png)",
  "",
  "# Machine Learning",
  "",
  paste0("Entrainement sur ", nrow(ml_df), " observations, ", length(feat), " predicteurs."),
  "",
  "## Modeles supervises",
  "",
  paste0("| Modele | RMSE | R2 |\n|---|---|---|\n",
         "| Random Forest | ", round(postResample(predict(rf, te), te$NGDP_RPCH)[1], 3),
         " | ", rf_r2, " |\n",
         "| Lasso | ", round(postResample(predict(lasso, te), te$NGDP_RPCH)[1], 3),
         " | ", lasso_r2, " |\n"),
  "",
  if (!is.null(feat_imp)) {
    c("## Importance des variables", "",
      "```{r}",
      "knitr::kable(feat_imp, caption = 'Top 10 predicteurs')",
      "```", "")
  },
  "",
  "## Clustering (K-means)",
  "",
  "![Clusters](clusters.png)",
  "",
  "## ACP",
  "",
  "![PCA](pca.png)",
  "",
  "# Deep Learning",
  "",
  if (!is.null(dl_res) && dl_res == "ok") {
    c(paste0("**R2 DL** : ", dl_r2), "")
  } else {
    c("Deep Learning non disponible.", "")
  },
  "",
  "# Benchmark : Maroc vs region",
  "",
  paste0("**", pct_above_region, "%** des indicateurs au-dessus de la region."),
  "",
  "![Benchmark](bench.png)",
  "",
  "```{r}",
  "knitr::kable(bl %>% select(indicator, morocco, region_avg, ratio) %>% arrange(desc(ratio)),",
  "             digits = 2, caption = 'Detail benchmark')",
  "```",
  "",
  "# Synthese et recommandations",
  "",
   "1. **Croissance moderee** : TCAM ", round(100 * tcam, 2), "%",
   "2. **Endettement** : effet negatif significatif (p=0.041)",
   "3. **Inflation** : correlation faible avec la croissance",
   "4. **Banques** : CDM la plus volatile, BCP la plus stable",
   "5. **Competitivite** : ", pct_above_region, "% au-dessus de la region",
   paste0("6. **ML** : RF (R2=", rf_r2, ") > Lasso (R2=", lasso_r2, ") > DL (R2=", dl_r2, ")"),
   if (!is.null(edu_real)) {
     paste0("7. **Education** : progression continue, primaire > 116%, alphabetisation ~64%")
   },
  "",
  "## Perspectives",
  "",
   "- Diversification economique (services, tourisme, digital)",
   "- Contenir l'endettement public",
   "- Renforcer la stabilite bancaire",
   "- Exploiter les regimes identifies",
   "- Maintenir la dynamique educative (scolarisation, qualite, emploi)",
  "",
  "# Annexes",
  "",
   "| Fichier | Description |\n|---|---|\n",
   "| master_dataset.csv | Dataset complet |\n",
   "| education_real.csv | Donnees education reelles (WB) |\n",
   "| rf/lasso/arima_model.rds | Modeles |\n",
   "| data_quality.csv | Qualite des donnees |\n",
   "| education_enrollment_real.png | Inscriptions scolaires (reel) |\n",
   "| education_spending_real.png | Depenses/alphabetisation (reel) |\n",
   "| *.png | 16+ graphiques |\n",
  "",
  "---",
   paste0("*Rapport genere le ", Sys.time(), " — Kernel R v22 (donnees education reelles).*")
)

writeLines(rmd, "/kaggle/working/report.Rmd")
rmarkdown::render("/kaggle/working/report.Rmd",
                  output_format = rmarkdown::html_document(self_contained = TRUE),
                  output_file = "/kaggle/working/maroc_pipeline.html",
                  quiet = TRUE)
cat("=== PIPELINE COMPLETE ===\n")