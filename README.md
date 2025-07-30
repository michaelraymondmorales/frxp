# **FractalExplorerVAE**

![FractalExplorerVAE Banner](docs/anglemap.jpg)

## **Table of Contents**

* About the Project 
* Features
* Project Structure
* Getting Started
  * Prerequisites  
  * Installation
  * Running the CLI 
* Usage
  * Seed Management  
  * Image Management  
  * Rendering Fractals  
* Future Work
* Contributing
* License
* Contact

## **About the Project**

This project is a Python-based **Fractal Explorer** designed to generate, manage, and explore various types of fractal images. It provides a Command-Line Interface (CLI) for interacting with fractal 'seeds', the mathematical parameters defining a fractal, and the generated image artifacts. Future plans include integrating Variational Autoencoders (VAEs) for latent space exploration and a web-based interface.

The core motivation behind this project is to dive into the infinite universe of fractals, understand their underlying mathematics, and build a system for systematic generation and analysis, particularly for machine learning applications.

## **Features**

* **Fractal Seed Management:**  
  * Add, retrieve, update, remove, and restore fractal parameters (seeds).  
  * Supports various fractal types (e.g., Julia, Mandelbrot) and powers.  
* **Generated Image Management:**  
  * Log metadata for generated fractal images (associated seed, resolution, colormap, aesthetic rating).  
  * Organize physical image files into active and removed states.  
* **CLI Explorer:**  
  * A user-friendly command-line interface for all management tasks.  
* **Extensible Architecture:**  
  * Designed with modularity in mind to easily integrate new fractal types, rendering engines, and machine learning models (VAEs).  
* **Unit Tested:** Core data management logic is covered by unit tests to ensure reliability.

## **Project Structure**

The project follows a clean, modular structure to facilitate development and future expansion:  
```
FractalExplorerVAE/
├── .gitignore                             # Specifies files/directories to ignore by Git
├── data/                                  # JSON metadata files for seeds and images
│   ├── active_fractal_images.json
│   ├── active_fractal_seeds.json
│   ├── removed_fractal_images.json
│   └── removed_fractal_seeds.json
├── docs/                                  # Supplemental documents
│   ├── anglemap.jpg                       # README banner image
│   └── julia_set_math.md                  # Julia mathematics notes
├── fractal_explorer_vae/                  # Main application source code (package)
│   ├── __init__.py                        # Makes 'fractal_explorer_vae' a package
│   │
│   ├── cli/                               # Command-Line Interface application
│   │   ├── __init__.py                    # Makes 'cli' a subpackage
│   │   ├── main.py                        # CLI entry point (argparse setup)
│   │   └── renderer.py                    # CLI-specific image rendering logic
│   │
│   ├── core/                              # Core domain logic and shared utilities
│   │   ├── __init__.py                    # Makes 'core' a subpackage
│   │   ├── coord_converter.py             # Utilities for coordinate transformations
│   │   ├── coord_generator.py             # Utilities for generating coordinate grids
│   │   ├── data_managers/                 # Subpackage for data management
│   │   │   ├── __init__.py                # Makes 'data_managers' a subpackage
│   │   │   ├── image_manager.py           # Manages image metadata (JSON) and files
│   │   │   └── seed_manager.py            # Manages fractal seed metadata (JSON)
│   │   └── fractal_calcs.py               # Numba fractal calculation functions
│   │
│   ├── vae/                               # Variational Autoencoder (VAE)(Future)
│   │   ├── __init__.py                    # Makes 'vae' a subpackage
│   │   ├── model.py                       # VAE model architecture
│   │   └── train.py                       # VAE training script
│   │
│   └── web_app/                           # Web application interface (Future)
│       ├── __init__.py                    # Makes 'web_app' a subpackage
│       └── app.py
├── LICENSE                                # MIT License
├── notebooks/                             # Jupyter notebooks for analysis and testing
│   └── README.md                          # Explanation of notebook contents
├── pyproject.toml                         # Project metadata and dependencies
├── README.md                              # This file
├── rendered_fractals/                     # Stores generated fractal images
│   ├── active/                            # Currently active images
│   │   └── .gitkeep                       # Placeholder to keep directory in Git
│   ├── removed/                           # Images moved to removed status
│   │   └── .gitkeep                       # Placeholder to keep directory in Git
│   └── staging/                           # Temporary directory for rendered images
│       └── .gitkeep                       # Placeholder to keep directory in Git
├── tests/                                 # Unit and integration tests
│   ├── test_CLI.py
│   ├── test_image_manager.py
│   └── test_seed_manager.py
```
## **Getting Started**

To get a local copy up and running, follow these simple steps.

### **Prerequisites**

* **Python:** This project requires Python 3.12.11   

  * If you need to manage multiple Python versions, consider using pyenv (macOS/Linux) or conda (Cross-platform).  

    * **pyenv:** Follow installation instructions at [pyenv/pyenv](https://github.com/pyenv/pyenv).  
    * **conda:** Download Miniconda or Anaconda from [conda.io/miniconda](https://docs.conda.io/en/latest/miniconda.html).

### **Installation**

1. **Clone the repo:**   
```bash
git clone https://github.com/michaelraymondmorales/FractalExplorerVAE.git  
cd FractalExplorerVAE
```
2. Create and activate a Python virtual environment:   

   It's highly recommended to use a virtual environment to manage project dependencies.   

Create venv using your desired Python version, Python 3.12.11 recommended.
```bash
python3 -m venv .venv 
```
Activate venv
```bash
# macOS/Linux: 
source .venv/bin/activate  

# Windows (Command Prompt):  
.venv\Scripts\activate.bat  

# Windows (PowerShell):  
.venv\Scripts\Activate.ps1
```

3. **Install PyTorch (Crucial for VAE/ML features):**  
   * **IMPORTANT:** PyTorch installation varies based on your OS and GPU setup.  
   * Visit the official PyTorch website's "Get Started" section: [pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)  
   * Use their selector to generate the pip install command specific to your system (e.g., CUDA 11.8, CPU only).  
   * **Run that command in your activated virtual environment.**  
   * *Example (for CUDA 11.8):* pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118  
   * *Example (for CPU only):* pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu  
4. Install project dependencies and CLI:  

   This command installs all other dependencies listed in pyproject.toml and makes your fex CLI command available.   

```python
pip install -e .
```
### **Running the CLI**

Once installed, you can run the CLI from your project root:  
```bash
# Get general help 
fex --help
```
```bash
# Get help for seed commands  
fex seed --help
```
```bash
# Get help for image commands
fex image --help
```

## **Usage**

Here are some common commands to get started with the FractalExplorerVAE CLI.

### **Seed Management**

* **List all active seeds:**  
```bash
fex seed list
```
* **List all removed seeds:**  
```bash
fex seed list --status removed
```
* **List all seeds (active and removed):** 
```bash 
fex seed list --status all
```
* **Add a new Julia seed:**  
```bash
fex seed add   
    --type Julia   
    --subtype Standard   
    --power 2   
    --x_span 4.0 
    --y_span 4.0   
    --x_center 0.0 
    --y_center 0.0   
    --c_real 0.7 
    --c_imag 0.27015   
    --bailout 2.0 
    --iterations 600
```
* **Get details of a specific seed:**  
```bash
fex seed get seed_00001
```
* **Update a seed's iterations:**  
```bash
fex seed update seed_00001 --iterations 800
```
* **Remove a seed (moves to 'removed' status):**  
```bash
fex seed remove seed_00001
```
* **Restore a seed (moves back to 'active' status):**  
```bash
fex seed restore seed_00001
```
### **Image Management**

* **Render and add an image from a seed:**  
```bash
fex image render seed_00001   
    --resolution 1024  
    --colormap viridis   
    --rendering_type iterations   
    --aesthetic_rating human_friendly
```
* **List all active images:** 
```bash 
fex image list
```
* **List images filtered by aesthetic rating:**  
```bash
fex image list --aesthetic_filter human_friendly
```
* **List all images (active and removed) filtered by resolution:**  
```bash
fex image list --status all --resolution_filter 512
```
## **Future Work**

* **Variational Autoencoder (VAE) Integration:**  
  * Train VAEs on generated fractal images to explore their latent space.  
  * Generate new fractals by sampling from the VAE's latent space.  
  * Develop CLI commands for VAE training, evaluation, and generation.  
* **Web-based Interface:**  
  * Create a user-friendly web application for visual exploration and management of fractals.  
* **More Fractal Types:**  
  * Expand support for other fractal types (e.g., Burning Ship, Newton Fractals, Fractal Flames).  
* **Advanced Rendering Options:**  
  * Implement different coloring algorithms and visual effects.

## **Contributing**

Contributions are welcome\! If you have suggestions for improvements, new features, or bug fixes, please open an issue or submit a pull request.

## **License**

This project is licensed under the [MIT License](LICENSE).

## **Contact**

Michael Raymond Morales  
E-mail: michaelraymondmorales@gmail.com  
Project Link: https://github.com/michaelraymondmorales/FractalExplorerVAE  
LinkedIn Profile: https://linkedin.com/in/raymond-morales-172702368  