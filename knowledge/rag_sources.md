
# LearnLoop Knowledge Pack: Introduction to RAG

## S1: What is RAG?
Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with a language model. Before generating an answer, the system retrieves relevant information from an external knowledge source and provides it to the language model as context.

RAG helps language models answer questions using information that may not have been included in their original training data.

## S2: Why use RAG?
Language models can produce incorrect or outdated information. RAG can reduce this problem by retrieving relevant information from trusted documents.

It also allows knowledge to be updated by changing the external document collection without retraining the language model.

## S3: Main components
1. Documents: PDFs, text files, websites or other knowledge sources.
2. Chunking: Splitting large documents into smaller sections.
3. Embeddings: Numerical representations of text that capture semantic meaning.
4. Vector database: Stores embeddings and helps find semantically similar content.
5. Retriever: Finds relevant document chunks for a user's question.
6. Language model: Uses the retrieved information to generate a response.

## S4: How RAG works
1. Documents are collected and split into smaller chunks.
2. Each chunk is converted into an embedding.
3. Embeddings are stored in a vector database.
4. A user submits a question.
5. The question is converted into an embedding.
6. The retriever searches for relevant chunks.
7. Retrieved chunks are added to the language model's prompt.
8. The language model generates an answer using the provided context.

## S5: Practical example
Imagine a college has 500 pages of admission rules. A student asks: "What documents are required for admission?"

A RAG system searches the admission documents, retrieves the relevant sections and gives them to a language model. The model then creates an answer based on those sections.

## S6: Limitations
- Incorrect or incomplete documents can produce incorrect answers.
- Poor retrieval can miss important information.
- Large documents need careful chunking.
- Retrieval and generation add processing time and cost.
- RAG does not guarantee that every generated answer is correct.

## S7: Important distinction
RAG does not automatically retrain or permanently change the language model's weights when it retrieves a document. It supplies relevant information as context for that particular generation request.
