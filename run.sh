#!/bin/bash

# Assign a container name
CONTAINER_NAME="my_container"
IMAGE_NAME="my_tests"

# Step 1: Build Docker image
docker build -t $IMAGE_NAME .

# Step 2: Run Docker container with port mapping and container name
docker run -d -p 1337:1337 --name $CONTAINER_NAME $IMAGE_NAME

# Step 3: Wait for the Python process inside the container to complete
docker exec $CONTAINER_NAME bash -c "pytest"
sleep 2
# Step 4: Open reports page in browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:1337
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    start "" "http://localhost:1337"
else
    echo "Unsupported operating system. Please open a browser and navigate to http://localhost:1337 manually."
fi

# Step 5: Stop the container after 1 minute
sleep 60  # Wait for 1 minute

# Step 6: Stop and remove the container
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME

# Step 7: Delete the Docker image
docker rmi $IMAGE_NAME