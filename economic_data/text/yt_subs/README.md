---
annotations_creators:
- no-annotation
language_creators:
- machine-generated
language:
- ar
license:
- cc-by-4.0
multilinguality:
- monolingual
pretty_name: Moroccan Darija YouTube Subtitles
size_categories:
- 0<n<300
source_datasets:
- original
task_categories:
- other
task_ids:
- language-modeling
---

# Moroccan Darija YouTube Subtitles Dataset

This dataset contains subtitles from YouTube videos in Moroccan Darija, a colloquial Arabic dialect spoken in Morocco. The subtitles were collected from several popular Moroccan YouTube channels, providing a diverse set of transcriptions in the Darija language.

## Dataset Description

The dataset is provided as a CSV file, where each row represents a YouTube video and contains the following columns:
- `video_id`: The unique identifier of the YouTube video.
- `title`: The title of the YouTube video.
- `transcript`: The transcript of the video in Moroccan Darija without timestamps.

The subtitles cover a wide range of topics, including entertainment, news, history, and more, offering a comprehensive representation of the Moroccan Darija language as used in YouTube content.

Original transcripts and srt file can be found [here](https://github.com/hbourbouh/bourbouh-moroccan-darija-youtube-subtitles).

## Dataset Structure

The dataset is a single CSV file named `moroccan_darija_subtitles.csv`. The CSV file has the following structure:

```
video_id,title,transcript
video1_id,Video 1 Title,Video 1 Transcript in Moroccan Darija
video2_id,Video 2 Title,Video 2 Transcript in Moroccan Darija
...
```

- The first row of the CSV file contains the column headers: `video_id`, `title`, and `transcript`.
- Each subsequent row represents a YouTube video and its corresponding subtitle information.

## License

This dataset is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). By using this dataset, you agree to the terms and conditions of the license.

## Contact

Bouaghad, El Hassan \
Bourbouh, Hamza

If you have any questions, suggestions, or issues regarding this dataset, please contact us at hamza@misi.ma.
