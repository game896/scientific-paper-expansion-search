# EMPG collector

The program collects scientific papers from one subfield (case study: the European Mathematical Psychology Group), decides which of them belong to the field and stores them in a local database as vectors. The idea and the workflow are described in [design.md](design.md).

## Running

The Gemini key is set in the `.env` file (an example configuration is in `.env.example`):

```
GEMINI_API_KEY=your_key_here
```

Collection is started with the `run` command, where the number is the maximum number of new papers to collect:

```
run 25
```

When `run` is started without a number, the program prints how it is used. The starting set (field, authors, papers, keywords) is in `seed.yaml`.

## How it works

1. The field description from `seed.yaml` is turned into a list of numbers (an embedding).
2. Papers by the seed authors, the seed papers and keyword search results are fetched from OpenAlex.
3. The title and abstract of each paper are turned into a list of numbers and compared with the field description. A close paper is accepted, a distant one is rejected, and for borderline cases Gemini decides whether the paper belongs to the field.
4. For an accepted paper, Gemini extracts concepts, and for authors and journals that appear repeatedly it writes short descriptions.
5. Authors who appear in three accepted papers become a source of new papers, so the field expands on its own.

## What is stored in the database

Data is stored in two places in the `data/` folder.

**`data/chroma` is the database.** It holds four kinds of records with the same shape: **an id, a text, a list of 768 numbers (the vector) and a few fields for display.** The vector is computed from the text, so texts with similar meaning have similar numbers. Relations between records are not stored; they are computed as closeness of vectors.

Paper (the text is the title and abstract):

```
id:      paper:W2045968318
text:    The Diffusion Decision Model: Theory and Data for Two-Choice Decision Tasks
         The diffusion decision model allows detailed explanations of behavior in ...
vector:  [-0.013, 0.005, 0.005, -0.106, 0.014, ...]   (768 numbers)
fields:  year 2007, journal Neural Computation, authors "Roger Ratcliff; Gail McKoon",
         doi 10.1162/neco.2008.12-06-420, relevance 0.8276, concepts "diffusion decision model; drift rate; ..."
```

Concept (the text is a definition written by Gemini):

```
id:      concept:diffusion-decision-model
text:    diffusion decision model: A mathematical framework for modeling two-choice decision tasks ...
vector:  [-0.005, -0.011, 0.001, -0.114, 0.011, ...]
fields:  name "diffusion decision model"
```

Author (the text is a description Gemini writes from the author's papers):

```
id:      author:A5024018318
text:    Roger Ratcliff focuses on understanding cognitive processing in two-choice decision tasks ...
vector:  [-0.029, 0.033, 0.016, -0.081, -0.025, ...]
fields:  name "Roger Ratcliff", papers 20
```

A journal has the same shape as an author (id `journal:S35223124`, the text describes what it publishes). The author names in a paper's fields are for display only; the "author - paper" relation is not recorded anywhere.

**`data/state.json` is a helper file** the program uses between runs. It records the date of the last run, the authors already fetched and, for every author and journal, the accepted papers they appeared in. These counts decide when an author gets a description and when they become a source of new papers.

```
"authors": { "A5xxxxxxxxx": { "name": "Gail McKoon", "paper_ids": ["paper:W1", "paper:W2", "paper:W3"] } }
```

Deleting the `data/` folder starts the collection from the beginning.
