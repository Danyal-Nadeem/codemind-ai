from typing import List, Dict


MAX_CHUNK_TOKENS = 400


def chunk_files(files: List[Dict]) -> List[Dict]:
    chunks = []

    for file in files:
        content = file["content"]
        filepath = file["path"]
        extension = file["extension"]

        if file["lines"] <= 50:
            chunks.append({
                "text": content,
                "filepath": filepath,
                "start_line": 1,
                "end_line": file["lines"],
                "chunk_type": "small_file",
            })
            continue

        lines = content.split("\n")
        current_chunk = []
        current_start = 1

        for i, line in enumerate(lines, 1):
            current_chunk.append(line)

            if len("\n".join(current_chunk)) > MAX_CHUNK_TOKENS * 4:
                chunks.append({
                    "text": "\n".join(current_chunk),
                    "filepath": filepath,
                    "start_line": current_start,
                    "end_line": i,
                    "chunk_type": "file_chunk",
                })
                current_chunk = []
                current_start = i + 1

        if current_chunk:
            chunks.append({
                "text": "\n".join(current_chunk),
                "filepath": filepath,
                "start_line": current_start,
                "end_line": len(lines),
                "chunk_type": "file_chunk",
            })

    return chunks


def chunk_parsed_code(parsed_chunks: List[Dict]) -> List[Dict]:
    chunks = []

    for item in parsed_chunks:
        chunks.append({
            "text": f"# {item['type']}: {item['name']}\n{item['code']}",
            "filepath": item["filepath"],
            "start_line": item["start_line"],
            "end_line": item["end_line"],
            "chunk_type": item["type"],
            "name": item["name"],
        })

    return chunks
