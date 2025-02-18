import requests


def test_upload_pdf():
    """PDFアップロードのテスト"""
    url = "http://localhost:8000/document/upload"
    files = {
        "file": (
            "test.pdf",
            open("test.pdf", "rb"),
            "application/pdf",
        )
    }

    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    test_upload_pdf()
