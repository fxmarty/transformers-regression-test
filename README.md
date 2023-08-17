# Transformers regression testing

This repo runs regression testing on transformers commits. [dana](https://github.com/google/dana) is used as a dashboard to visualize the data.

The regression tests are run automatically through GitHub Actions on a self-hosted runner.


## Run dashboard locally
To visualize the data locally:

```
git clone https://huggingface.co/datasets/fxmarty/transformers-regressions
cd transformers-regressions/dana
npm install
npm start
```

And go to http://localhost:7000 with username `admin` and password `admin`.

## Hosted dashboard

A dashboard is hosted at https://fxmarty-regression-testing.hf.space, but may not be up to date with the data (requires restart).
