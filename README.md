# What's for Dinner?

A full-stack application that suggests meals based on your available pantry items. It leverages the **Tinker API** to sample LLM-generated suggestions and uses the **Backboard API** to maintain a history of your recently selected meals, ensuring you don't get the same suggestion twice!

## Project Structure

- **`main.py`**: The FastAPI backend entry point. Provides `/api/suggest` for meal suggestions and `/api/select` to save your choice.
- **`frontend/`**: The frontend Vite + React application, styled using Tailwind CSS.
- **`train/`**: Scripts to fine-tune a LoRA model on custom meal suggestion data (`train.jsonl`).
- **`render.yaml` & `build.sh`**: Configuration and scripts to deploy the application easily on Render.

## Features

- **Meal Suggestions**: Input the ingredients you have, and get 3-4 creative meal ideas.
- **Smart History Tracking**: Integrates with Backboard API to store your recent dinner selections so the LLM knows what you've had recently and avoids repeating it.
- **Model Fine-Tuning Pipeline**: Includes a `train_lora.py` script to fine-tune a language model using the Tinker SDK with custom meal data.
- **Modern Tech Stack**: Fast and responsive, built with FastAPI, React, Vite, and Tailwind CSS.

## Prerequisites

- Python 3.11+
- Node.js (v16+ recommended)
- API Keys for **Tinker** and **Backboard**

## Local Development

### 1. Environment Setup

Create a `.env` file in the root directory and configure the following variables:

```env
BACKBOARD_URL=https://api.backboard.io/v1
BACKBOARD_API_KEY=your_backboard_api_key
TINKER_API_KEY=your_tinker_api_key
TINKER_SAMPLER_PATH=your/model/path/here
```

### 2. Run the Application

You can use the `build.sh` script to install all dependencies and build the frontend, or follow these steps:

#### Backend Setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend Setup

In a new terminal tab, navigate to the `frontend` directory:

```bash
cd frontend
npm install
npm run dev
```

### 3. Build for Production

To serve the frontend via the FastAPI app (as configured in `main.py`), you need to build the Vite app first:

```bash
cd frontend
npm run build
```

Then, running the backend will serve the static files from `frontend/dist` on `/`.

## Model Fine-Tuning

To train a LoRA model on your custom dataset:

```bash
cd train
# Make sure your Tinker credentials are set
python train_lora.py
```

You can test your fine-tuned model using `test.py`.

## Deployment

This repository is configured for easy deployment on [Render](https://render.com/). Just connect your repository and Render will automatically use `render.yaml` to configure and deploy the service.
