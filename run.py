import os
import uvicorn

os.environ.setdefault("CAMPUSBUDDY_LLM", "none")

if __name__ == "__main__":
    print("\n  CampusBuddy is live at: http://127.0.0.1:8000")
    print("  API Swagger docs at:    http://127.0.0.1:8000/docs\n")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
