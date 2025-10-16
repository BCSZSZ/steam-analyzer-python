# Steam Review Fetcher & Analyzer

This is a simple GUI application built with Python and CustomTkinter that allows you to fetch a specified number of user reviews for any Steam application and analyze the sentiment by language.

## Project Structure

The project is now organized into separate files for better maintainability:

- `main.py`: Contains all the code for the `CustomTkinter` graphical user interface (GUI).
- `backend.py`: Contains all the core logic for fetching data from the Steam API and for analyzing the review data.
- `requirements.txt`: Lists the necessary Python packages for the project.
- `.gitignore`: A standard git configuration to exclude unnecessary files from version control.

## Setup and Installation

This project is designed to be run within a Python virtual environment to keep dependencies isolated.

### 1\. Create a Virtual Environment

First, open your terminal or command prompt, navigate to the project directory, and create a virtual environment.

    # On macOS/Linux
    python3 -m venv venv

    # On Windows
    python -m venv venv

### 2\. Activate the Virtual Environment

Next, activate the newly created environment.

    # On macOS/Linux
    source venv/bin/activate

    # On Windows
    .\venv\Scripts\activate

You'll know it's active when you see `(venv)` at the beginning of your terminal prompt.

### 3\. Install Dependencies

With the virtual environment active, install the required Python packages using the `requirements.txt` file.

    pip install -r requirements.txt

## How to Run

After setting up the environment and installing the dependencies, you can run the application with a single command:

    python main.py

## Using Git

Now that this is a Git project, you can track your changes. Here are the basic steps to get your project onto your GitHub repository.

    # Step 1: Initialize a new Git repository in your project folder
    git init

    # Step 2: Add all the files to the staging area
    git add .

    # Step 3: Make your first commit
    git commit -m "Initial commit: Project setup with GUI and backend separation"

    # Step 4: Add your GitHub repository as the remote origin
    # Make sure to use the correct URL for your repo
    git remote add origin [https://github.com/BCSZSZ/steam-analyzer-python.git](https://github.com/BCSZSZ/steam-analyzer-python.git)

    # Step 5: Push your code to the main branch on GitHub
    git push -u origin main
