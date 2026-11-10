# Retrieval-Augmented Generation

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
