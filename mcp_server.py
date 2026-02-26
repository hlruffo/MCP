from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


# python sdk gerando mcp server
mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}


# Write a tool to read a doc
@mcp.tool(
    name="read_doc_contents",
    title="Read Docs",
    description="Read the contents of a document and return it as an string",
)
def read_documents(doc_id: str = Field(description="Id of the document to read")):
    if doc_id not in docs:
        raise ValueError(f"Document with {doc_id} not found")
    return docs[doc_id]


# Write a tool to edit a doc
@mcp.tool(
    name="edit_document",
    title="Edit documents",
    description="Edit the document by replacing a string in the documents content with a new string",
)
def edit_document(
    doc_id: str = Field(description="Id of the document to edit"),
    old_string: str = Field(
        description="The text to replace. Must match exactly, including white space"
    ),
    new_string: str = Field(
        description="The new text to insert in place of the old text"
    ),
):
    if doc_id not in docs:
        raise ValueError(f"Document with {doc_id} not found")

    docs[doc_id] = docs[doc_id].replace(old_string, new_string)
    return docs[doc_id]


# Write a resource to return all doc id's
@mcp.resource(
    "docs://documents",
    mime_type="application/json"
)
def list_docs() -> list[str]:
    return list(docs.keys())

# Write a resource to return the contents of a particular doc
@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain"
)
def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with {doc_id} not found")
    return docs[doc_id]


# Write a prompt to rewrite a doc in markdown format
@mcp.prompt(
    name="format",
    description="Rewrites the contents of a document into Markdown format"
)
def format_document(
    doc_id: str = Field(
        description="Id of the document to be transformed")
        ) -> list[base.Message]:
    prompt = f"""
        Your goal is to reformat a document to be written with markdown syntax.

        The id of the document you need to reformat is:
        <document_id>
        {doc_id}
        </document_id>

        Add in headers, bullet points, tables, etc as necessary. Feel free to add in structure.
        Use the 'edit_document' tool to edit the document. After the document has been reformatted...
    """
    
    return [base.UserMessage(prompt)]

# Write a prompt to summarize a doc
@mcp.prompt(
    name="summarize",
    description="Summarizes the contents of a document."
)
def summarize_document(
    doc_id: str = Field(
        description="Id of the document to be summarized")
        ) -> list[base.Message]:
    prompt = f"""
        Your goal is to summarize a document.

        The id of the document you need to summarize is:
        <document_id>
        {doc_id}
        </document_id>

        Use the 'read_doc_contents' tool to read the document, then provide a concise summary
        of its key points. The summary should be brief (2-4 sentences) and capture the most
        important information from the document.
    """

    return [base.UserMessage(prompt)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
