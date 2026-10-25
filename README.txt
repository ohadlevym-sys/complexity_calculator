# IPA Feature Complexity & Economy Calculator

A computational phonology web application built to analyze and calculate segment-feature economy and phonological complexity scores across linguistic inventories. The tool bridges theoretical phonology and linear programming to extract minimal contrastive feature matrices and visualize structural relationships.

## Core Features
* **Minimal Feature Set Optimization:** Uses Binary Linear Programming (via PuLP) to compute the most economical feature matrix required to distinguish all segments in a given inventory.
* **Feature Geometry Trees:** Dynamically builds and visualizes hierarchical feature trees for individual IPA segments using Graphviz.
* **PHOIBLE Database Integration:** Search, import, and normalize phonological inventories directly from PHOIBLE.
* **Scoring Models:** Evaluates inventories using multiple theoretical models, including Relative, Exploitation, and Frugality scores, visualized via Plotly.
* **Manual Inventory Testing:** Input custom IPA segment lists, normalized dynamically to resolve diacritic and unicode inconsistencies.

## Tech Stack
* **Frontend:** Streamlit, Plotly
* **Data Processing & Logic:** Python, Pandas
* **Mathematical Optimization:** PuLP
* **Graph Visualization:** Graphviz

## Installation

1. Clone this repository:
    git clone https://github.com/ohadlevym-sys/complexity_calculator.git
    cd complexity_calculator

2. Install the required dependencies:
    pip install -r requirements.txt

(Note: Graphviz must also be installed on your system path for tree generation to work).

## Usage

Launch the interactive web application locally:
    streamlit run app.py