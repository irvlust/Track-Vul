async def create_app(client, name="TestApp"):
    files = {
        "requirements": ("requirements.txt", b"fastapi==0.103.0\nuvicorn>=0.23.0,<0.24.0")
    }
    data = {
        "name": name,
        "description": "Test app with deps"
    }

    response = await client.post("/application", data=data, files=files)
    assert response.status_code == 200
    return response