The TAC Relation Extraction Dataset (TACRED)
=============

This repository contains basic information of the Stanford TACRED dataset (v1.0). TACRED is a large-scale relation extraction dataset with 119,474 examples, created mainly via crowdsourcing, reusing the TAC KBP relation types. For detailed information about the dataset and benchmark results, please refer to [the TACRED paper](https://nlp.stanford.edu/pubs/zhang2017tacred.pdf).

## Dataset Collection

The dataset was created based on query entities and annotated system reponses in the yearly TAC Knowledge Base Population (TAC KBP) evaluations. In each year of the evaluation (2009 - 2014), 100 entities (people or organizations) are given as queries (i.e., subjects), for which participating systems should find associated relations and object entities. Sentences that contain query entities in the evaluation corpus were sampled. Each sentence was then crowd-annotated using Mechanical Turk, where each turk annotator was asked to annotate the subject and object entity spans, and the corresponding relation (out of the 41 possible relation types and a special `no_relation` type). Note that negative examples (i.e., examples with `no_relation` type) encountered in the annotation process are fully included in the dataset, resulting in a negative ratio of about 78.68%.

For more information on the collection and validation of the dataset, please refer to the paper.

## Dataset Statistics

The dataset is stratified into training, development and test splits. To encourage statistical models to learn entity and topic-agnostic features, the stratification is done based on the year in which the corresponding TAC KBP challenge happened. Information for each split is listed as follows:

| Split | # Examples | TAC KBP Year |
| ----- | ----- | ----- |
| Train | 75,050 | 2009 - 2012 |
| Dev | 25,764 | 2013 |
| Test | 18,660 | 2014 |

For detailed per-relation statistics, please refer to the `tacred.stats` file.

## Data Format

#### CoNLL format

By default the data is in a format similar to that used in the CoNLL shared tasks. For each example, the first line is in the format of `# id=ID docid=DOCID reln=RELATION`, where `ID` is a unique hash code of the current example, `DOCID` is the LDC document id from which this example was drawn, and `RELATION` is the relation type. Each following line consists of the following tab-seperated fields:

- `index`: 1-based index of the current token.
- `token`: the token sequence in the sentence.
- `subj`: whether the current token is part of a subject (denoted by `SUBJECT`) or not (denoted by `-`). 
- `subj_type`: named entity type of the current token, if it is a subject (otherwise is `-`).
- `obj`: whether the current token is part of an object (`OBJECT`) or not (`-`).
- `obj_type`: named entity type of the current token, if it is an object (otherwise is `-`).
- `stanford_pos`: part-of-speech tag of the current token.
- `stanford_ner`: named entity tag of the current token.
- `stanford_deprel`: dependency relation of the current token to its head token.
- `stanford_head`: 1-based index of the dependency head of the current token.

The last 4 fields were generated by running [the Stanford CoreNLP v3.7.0](https://stanfordnlp.github.io/CoreNLP/) on the token sequence of each example.

#### JSON format

JSON format files can be created into a `json/` folder by running the following script:

```
python scripts/generate_json.py ./conll ./json
```

Note that the JSON files use `subj_start` and `subj_end` instead of the `subj` field (same for the `obj` field).

## Scoring

In addition to the original dataset files, gold relation labels in each dataset split are also stored in the `gold/` folder. To score system predictions using precision, recall and F1 metrics, the following script can be run:

```
python scripts/score.py GOLD_FILE PRED_FILE
```

Here the `PRED_FILE` must be in the same format as the gold file, with each relation per line.

## Citation

Please cite the following paper if you use TACRED in your research:

```
@inproceedings{zhang2017tacred,
 author = {Zhang, Yuhao and Zhong, Victor and Chen, Danqi and Angeli, Gabor and Manning, Christopher D.},
 booktitle = {Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing (EMNLP 2017)},
 title = {Position-aware Attention and Supervised Data Improve Slot Filling},
 url = {https://nlp.stanford.edu/pubs/zhang2017tacred.pdf},
 year = {2017}
}
```

## License

The TACRED dataset is licensed by the [Linguistic Data Consortium](https://www.ldc.upenn.edu/).