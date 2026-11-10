"""Builds the small sample corpus used by the tests, the demo and the evaluation.
ALL TEXT IS ORIGINAL (written for this project), so the files can be redistributed freely.
Usage: python evaluation/build_sample_docs.py   -> writes sample_data/*"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parents[1] / "sample_data"

ML_FUNDAMENTALS = [  # one string per PDF page
    ("Supervised Learning",
     "Supervised learning trains a model on labeled examples. Every training example pairs an input with a known target value, "
     "and the learning algorithm searches for a function that maps inputs to targets. The two main supervised tasks are "
     "classification, where the target is a category such as spam or not spam, and regression, where the target is a continuous "
     "number such as a house price. A model is judged by how well it predicts targets for examples it has never seen. "
     "Overfitting happens when a model memorises noise and quirks of the training set, so training error becomes very low while "
     "error on new data stays high. Underfitting is the opposite problem: the model is too simple to capture the real pattern."),
    ("Unsupervised Learning",
     "Unsupervised learning looks for structure in data that has no labels. Clustering groups similar items together, and "
     "K-means is a popular clustering algorithm that repeatedly assigns each point to its nearest centroid and then moves each "
     "centroid to the mean of its assigned points. The number of clusters K must be chosen by the practitioner. Dimensionality "
     "reduction compresses many features into a few while keeping the most important variation; principal component analysis (PCA) "
     "does this by projecting data onto directions of maximum variance. Unlike supervised learning, there is no single correct "
     "answer to check against, so evaluation relies on internal measures such as cluster cohesion or on human judgement."),
    ("Evaluating Classifiers",
     "Accuracy is the fraction of predictions that are correct, but it can be misleading when classes are imbalanced. Precision is "
     "the fraction of predicted positives that are truly positive, and recall is the fraction of true positives that the model "
     "finds. The F1 score is the harmonic mean of precision and recall. Cross-validation estimates generalisation by splitting the "
     "data into k folds, training on k-1 folds and testing on the remaining fold, then averaging the k results. A held-out test set "
     "must never be used for tuning, otherwise the reported score is optimistically biased."),
    ("Bias, Variance and Regularization",
     "The bias-variance tradeoff describes two sources of error. High bias means the model makes strong simplifying assumptions and "
     "underfits. High variance means the model is very sensitive to the particular training sample and overfits. Regularization "
     "reduces variance by penalising model complexity. L2 regularization, also called ridge, adds the sum of squared weights to the "
     "loss, while L1 regularization, also called lasso, adds the sum of absolute weights and can drive some weights exactly to zero, "
     "which performs feature selection. Early stopping and gathering more training data also reduce overfitting."),
]
NEURAL_NETWORKS = [
    ("Neurons and Activation Functions",
     "An artificial neuron computes a weighted sum of its inputs, adds a bias term, and passes the result through an activation "
     "function. Without a non-linear activation function, a stack of layers would collapse into a single linear transformation. "
     "The ReLU activation, defined as the maximum of zero and the input, is widely used in hidden layers because it is cheap to "
     "compute and reduces the vanishing gradient problem. The sigmoid squashes values into the range zero to one and is often used "
     "for binary outputs, while softmax turns a vector of scores into a probability distribution over classes."),
    ("Training with Backpropagation",
     "Neural networks are trained by minimising a loss function. Backpropagation applies the chain rule of calculus to compute the "
     "gradient of the loss with respect to every weight, moving backwards from the output layer. Gradient descent then updates each "
     "weight by subtracting the learning rate multiplied by its gradient. A learning rate that is too large makes training diverge, "
     "while one that is too small makes it very slow. Stochastic gradient descent estimates the gradient from a small mini-batch of "
     "examples, and the Adam optimizer adapts the step size for each weight using running averages of past gradients."),
    ("Convolutional and Recurrent Networks",
     "Convolutional neural networks (CNNs) are designed for grid-like data such as images. They apply small learnable filters that "
     "slide across the input, so the same pattern detector is reused at every position, and pooling layers reduce spatial size. "
     "Recurrent neural networks (RNNs) process sequences by carrying a hidden state from one step to the next, which lets them use "
     "earlier context. Plain RNNs struggle with long sequences because gradients vanish, which motivated gated designs such as the "
     "LSTM. Transformers replaced recurrence with self-attention, allowing all positions in a sequence to be processed in parallel."),
]
RAG_SYSTEMS_MD = """# Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) combines a retrieval component with a language model. Instead of relying only on knowledge
stored in the model weights, the system first retrieves passages from an external document collection and gives them to the model
as context for its answer.

## Why RAG is used

Language models can produce fluent but unsupported statements, often called hallucinations. Supplying retrieved evidence lets the
model ground its answer in documents and lets the user check the cited sources. RAG also allows knowledge to be updated by
changing the document collection, without retraining the model.

## Chunking

Documents are split into chunks before indexing. Chunk size is a tradeoff: very small chunks lose surrounding context, while very
large chunks dilute the embedding and waste the model's context window. Overlap between neighbouring chunks reduces the chance
that an answer is cut in half at a boundary.

## Embeddings and vector databases

An embedding model maps text to a vector so that texts with similar meaning lie close together. A vector database stores these
vectors and answers nearest-neighbour queries, usually with cosine similarity. Metadata such as the source filename and page
number is stored with each vector so that answers can cite where the evidence came from.

## Agentic RAG

An agentic RAG system adds a controller that decides what to do with a request. The agent classifies the intent of the user,
chooses a tool such as search, summarisation or quiz generation, retrieves evidence, checks whether the evidence is sufficient,
and only then asks the language model to write the response. If no relevant evidence is found, a well-behaved agent says so
instead of inventing an answer. Limits on the number of steps prevent endless loops.
"""


def build_pdf(path: Path, pages):
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle(path.stem.replace("_", " ").title())
    for title, body in pages:
        c.setFont("Helvetica-Bold", 15)
        c.drawString(50, 790, title)
        c.setFont("Helvetica", 11)
        y = 760
        for line in simpleSplit(body, "Helvetica", 11, 495):
            c.drawString(50, y, line)
            y -= 16
        c.showPage()
    c.save()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build_pdf(OUT / "ml_fundamentals.pdf", ML_FUNDAMENTALS)
    build_pdf(OUT / "neural_networks.pdf", NEURAL_NETWORKS)
    (OUT / "rag_systems.md").write_text(RAG_SYSTEMS_MD, encoding="utf-8")
    (OUT / "README.md").write_text(
        "# Sample documents\n\nOriginal text written for ScholarMind AI (no third-party content), free to redistribute.\n"
        "Regenerate with `python evaluation/build_sample_docs.py`.\n\n"
        "- `ml_fundamentals.pdf` (4 pages): supervised/unsupervised learning, evaluation, bias-variance\n"
        "- `neural_networks.pdf` (3 pages): neurons, backpropagation, CNN/RNN\n"
        "- `rag_systems.md`: RAG, chunking, embeddings, agentic RAG\n", encoding="utf-8")
    print("built:", sorted(p.name for p in OUT.iterdir()))
