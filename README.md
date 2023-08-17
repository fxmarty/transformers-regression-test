# Transformers regression testing

This repo runs regression testing on transformers commits. [dana](https://github.com/google/dana) is used as a dashboard to visualize the data.

The regression tests are run automatically through GitHub Actions on a self-hosted runner.

To visualize the data locally:

```
git clone https://huggingface.co/datasets/fxmarty/transformers-regressions
cd transformers-regressions/dana
npm install
npm start
```

And go to http://localhost:7000 with username `admin` and password `admin`.
