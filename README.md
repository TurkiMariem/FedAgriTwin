# FedAgriTwin
This repository contains the source code used to evaluate the FedAgriTwin solution
1) Digital Twin
For the Digital Twin (DT) component, it is essential to :

a-  run the model using the flask server

Make sure you have Python and pip installed. Then, install the required packages:

pip install -r requirements.txt

Run the Flask Server

Launch the Flask server to serve the model:

python app.py
This will start the server at http://localhost:5000

b-   Install and run the Eclipse Ditto environment 

Use the Docker image available at the following link: https://github.com/eclipse-ditto/ditto.git
 Once the Ditto instance is running, the DT configuration can be initialized via Postman by importing a predefined JSON file. This JSON file automates several critical tasks, including:
 
**The creation of access policies

**The definition of digital twins (things)

**The configuration of communication connections

**The dynamic update of thing attributes.


2) Federated Learning
   
To run the federated learning experiment:

Open the notebook: Crop_federated.ipynb.

Locate the cell where the dataset is loaded and edit the path to point to your local copy of Crop_recommendation.csv.

Run the notebook cells sequentially and enjoy the execution process.


