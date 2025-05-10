import aiohttp
import json
import aiomysql


# Tool definition
async def query_mysql(query_string: str) -> str:
    conn = await aiomysql.connect(
        host="localhost",
        user="root",
        password="root",
        db="test"
    )
    async with conn.cursor() as cur:
        await cur.execute(query_string)
        rows = await cur.fetchall()
    await conn.ensure_closed()
    return str(rows)


# Agent function using Ollama
async def run_agent(user_query: str) -> str:
    functions = [
        {
            "name": "query_mysql",
            "description": "Query the MySQL database with a raw SQL string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_string": {"type": "string"}
                },
                "required": ["query_string"]
            }
        }
    ]

    async with aiohttp.ClientSession() as session:
        # Step 1: Send user query to LLM
        async with session.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": "qwen2:7b",
                "messages": [{"role": "user", "content": user_query}],
                "tools": functions,
                "tool_choice": "auto",
                "stream": False
            }
        ) as resp:
            result = await resp.json()

        tool_call = result["choices"][0].get("message", {}).get("tool_calls", [{}])[0]
        if tool_call:
            args = json.loads(tool_call["function"]["arguments"])
            tool_result = await query_mysql(args["query_string"])

            # Step 2: Feed tool result back to LLM for summarization
            messages = [
                {"role": "user", "content": user_query},
                {"role": "tool", "tool_call_id": tool_call["id"], "name": "query_mysql", "content": tool_result}
            ]

            async with session.post(
                "http://localhost:11434/v1/chat/completions",
                json={
                    "model": "qwen2:7b",
                    "messages": messages,
                    "stream": False
                }
            ) as resp2:
                final_result = await resp2.json()
                return final_result["choices"][0]["message"]["content"]
        else:
            return result["choices"][0]["message"]["content"]
