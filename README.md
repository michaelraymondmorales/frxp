# **frxp**

![FractalExplorerVAE Banner](docs/images/anglemap.jpg)

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

This project is a Python-based **Fractal Explorer** designed to generate, manage, and explore various types of fractal images. It provides a Command-Line Interface (CLI) for interacting with fractal 'seeds', the mathematical parameters defining a fractal, and the generated image artifacts. The project is designed with a clear separation of a Python backend and a React frontend, which currently features a **3D interactive landscape of the generated fractals**. Future plans include integrating Variational Autoencoders (VAEs) for latent space exploration. 

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
├── LICENSE  
├── README.md  
├── backend  
│   ├── data  
│   │   ├── active\_fractal\_images.json  
│   │   ├── active\_fractal\_seeds.json  
│   │   ├── removed\_fractal\_images.json  
│   │   └── removed\_fractal\_seeds.json  
│   ├── frxp  
│   │   ├── cli  
│   │   │   ├── main.py  
│   │   │   └── renderer.py  
│   │   ├── core  
│   │   │   ├── coord\_converter.py  
│   │   │   ├── coord\_generator.py  
│   │   │   ├── data\_managers  
│   │   │   │   ├── image\_manager.py  
│   │   │   │   └── seed\_manager.py  
│   │   │   ├── fractal\_calcs.py  
│   │   │   ├── lch\_color.py  
│   │   │   ├── normalize\_maps.py  
│   │   │   └── utilities.py  
│   │   ├── vae  
│   │   │   ├── \_\_init\_\_.py  
│   │   │   ├── vae\_models.py  
│   │   │   └── vae\_train.py  
│   │   └── webapp  
│   │       ├── \_\_init\_\_.py  
│   │       └── app.py  
│   └── tests  
│       ├── test\_cli.py  
│       └── test\_data\_managers.py  
├── docs  
│   └── anglemap.jpg  
├── frontend  
│   ├── public  
│   └── src  
│       ├── App.jsx  
│       ├── index.css  
│       └── main.jsx  
├── notebooks  
│   └── README.md  
└── pyproject.toml
```
## **Getting Started**

To get a local copy up and running, follow these simple steps.

### **Prerequisites**

* **Python:** This project requires Python 3.8 or higher.  
* **Node.js:** The frontend requires Node.js (recommended LTS version).  
* **Git:** You'll need Git installed to clone the repository.

### **Installation**

1. Clone the repository:  
   git clone https://github.com/your-username/frxp.git  
   cd frxp

2. Install backend dependencies:  
   cd backend  
   pip install \-e .

3. Install frontend dependencies:  
   cd ../frontend  
   npm install

### **Running the CLI**

The CLI can be run from the backend directory. 
```bash 
# Example: Adding a new Mandelbrot seed  
python -m frxp.cli.main seed add 
  --type Mandelbrot 
  --subtype Standard 
  --power 2
  --x_span 4.0
  --y_span 4.0
```
```bash
# Example: Rendering an image from a specific seed  
python -m frxp.cli.main image render 
  --seed_id seed_00001 
  --resolution 1024 
  --colormap twilight 
  --rendering_type iterations
```

## **Usage**

### **Seed Management:**  
  * Add a new seed: 
```bash
python -m frxp.cli.main seed add [options] 
```
  * List all seeds: 
```bash
python -m frxp.cli.main seed list
```
  * Get details of a seed:
```bash
python -m frxp.cli.main seed get [seed_id]
``` 
  * Remove a seed: 
```bash
python -m frxp.cli.main seed remove [seed_id]
```  
### **Image Management:**  
  * List all images:
```bash
python -m frxp.cli.main image list
```
  * Get details of an image:
```bash
python -m frxp.cli.main image get [image_id] 
``` 
  * Render an image from a seed:
```bash 
python -m frxp.cli.main image render [options]
```

## **Future Work**

* **API Integration:** Clean up the large App.jsx file and integrate it with the backend API for dynamic fractal rendering.  
* **Variational Autoencoder (VAE) Integration:**  
  * Train VAEs on generated fractal images to explore their latent space.  
  * Generate new fractals by sampling from the VAE's latent space.  
  * Develop CLI commands for VAE training, evaluation, and generation.  
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
Project Link: https://github.com/michaelraymondmorales/frxp  
LinkedIn Profile: https://linkedin.com/in/raymond-morales-1727023