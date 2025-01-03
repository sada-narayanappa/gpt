import re
from collections import (
    Counter,
    defaultdict,
)
from langchain_core.documents import Document

NUM_TO_DOC: dict = {0: "Document Name", 1: "Chapter", 2: "Section", 3: "SubSection", 4: "SubSubSection"}
WHITESPACE_HEADER: dict = {72: "Paragraph", 101: "Chapter", 105: "Section", 116: "SubSection", 126: "SubSubSection"}
DOC_TO_NUM: dict = {"Document Name": 0, "Chapter": 1, "Section": 2, "SubSection": 3, "SubSubSection": 4}
TABLE_SETTINGS: dict = {"vertical_strategy": "lines", "horizontal_strategy": "lines", "snap_tolerance": 2}


"""
    Converts chunks of texts and metadata into Document objects.

    Args:
        chunks (list[dict]): list of dicts of formatted chunk text and the page number of the beginning of chunk
        document_name (str): the name of the document from which the chunks were extracted

    Returns:
        list[Document]: returns list of Document objects describing the chunks and their metadata
"""
def chunks_to_doc_obj(chunks: list[dict], document_name: str) -> list[Document]:
    return [Document(page_content=c["text"], metadata={"source": document_name, "page": c["page"]}) for c in chunks]


"""
Merge records that are part of a paragraph.

Args:
    records (list[dict]): document text lines.

Returns:
    list[dict]: merged text lines that are part of a paragraph.
"""
def merge_records(records: list[dict]) -> list[dict]:
    start = 0
    end = 0
    merge_list = []

    paragraph_tol = Counter(
        round(records[i + 1]["doctop"] - records[i]["doctop"]) for i in range(len(records) - 1)
    ).most_common()[0][0]

    for i, record in enumerate(records):

        if record["header_type"] != "Paragraph":
            merge_list.append(record)

        elif i >= end:

            start = i
            end = i + 1

            while (
                end < len(records)
                and (records[end]["header_type"] == "Paragraph")
                and (round(records[end]["doctop"] - records[end - 1]["doctop"]) <= paragraph_tol)
            ):
                end += 1

            merge_list.append(
                {
                    "header_type": "Paragraph",
                    "text": " ".join((r["text"] for r in records[start:end])),
                    "doctop": records[start]["doctop"],
                    "page_number": records[start]["page_number"],
                },
            )

    return merge_list


"""
    Convert records into a dictionary with header as keys and paragraphs as values.

    Args:
        records (list[dict]): list of dictionary containing paragraph and headers.
        document_name (str): string name

    Returns:
        dict[list]: return header: paragraph with page number appended at beginning dictionary
"""
def metadata_chunks(records: list[dict], document_name: str) -> dict[list]:
    chunk_dict = defaultdict(list)

    metadata = [f"Document Name: {document_name}"]

    for rec in records:

        if rec["header_type"] != "Paragraph":

            num = DOC_TO_NUM.get(rec["header_type"])
            doc_header_type = metadata[-1].split(":")[0]
            metadata_num = DOC_TO_NUM.get(doc_header_type)

            while metadata_num >= num:
                metadata.pop()
                doc_header_type = metadata[-1].split(":")[0]
                metadata_num = DOC_TO_NUM.get(doc_header_type)

            name = f"{rec['header_type']}: {rec['text']}"

            metadata.append(name)

        else:
            chunk_dict[tuple(metadata)].append(str(rec["page_number"]) + " " + rec["text"])

    return chunk_dict


"""
Converts metadata dict into  a list of chunks. Uses max_char_limit to limit the number of characters per chunk.

Args:
    chunk_dict (dict[list]): dictionary containing headers as keys and paragraphs as values with page numbers appended at beginning of paragraphs.
    tokens (int, optional): chunk token limit . Defaults to 200.

Returns:
    list[dict]: list of dictionaries containing the chunk and page number
"""
def chunk_dict_to_list(chunk_dict: dict[list], tokens: int = 200) -> list[dict]:

    bge_tokens = 400
    tokens = bge_tokens if tokens >= bge_tokens else 200

    max_char_limit = tokens * 4

    chunks = []

    new_chunk = True
    page = None

    for k, paragraphs in chunk_dict.items():
        meta_data = "\n".join(k)
        page_num, paragraph = map(list, zip(*(s.split(" ", 1) for s in paragraphs)))
        page_num = [int(x) for x in page_num]
        small_paragraph = sum(len(i) for i in paragraph)

        if (len(meta_data) + small_paragraph) <= max_char_limit:
            small_paragraph = " ".join(paragraph)
            chunks.append({"text": meta_data + "\n\n" + small_paragraph, "page": page_num[0]})
            new_chunk = True
            continue

        for i, chunk in enumerate(paragraph):
            chunk_length = len(meta_data) + len(chunk)

            if new_chunk:
                page = page_num[i]
                new_chunk = False

            if chunk_length > max_char_limit:

                sentence_list = re.split("([?!.])", chunk)
                minichunk = meta_data + "\n\n"

                for sentence in sentence_list:

                    if len(minichunk) + len(sentence) > max_char_limit:
                        chunks.append({"text": minichunk, "page": page})
                        page = page_num[i]
                        minichunk = meta_data + "\n\n" + sentence

                    else:
                        minichunk += sentence

            else:
                chunks.append({"text": meta_data + "\n\n" + chunk, "page": page})
                new_chunk = True

    return chunks
