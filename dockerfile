# Base image with Chrome browser and Python
FROM python:3.9-slim-buster

# Install Chrome browser dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set up Chrome browser
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable

# Install additional dependencies for xdg-open
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy your repository to the working directory
COPY . /app

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install pytest and Allure
RUN pip install --no-cache-dir pytest allure-pytest

# Set up Allure
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

RUN wget -O allure-2.15.0.tgz https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.15.0/allure-commandline-2.15.0.tgz \
    && tar -xzf allure-2.15.0.tgz -C /opt \
    && ln -s /opt/allure-2.15.0/bin/allure /usr/bin/allure \
    && rm allure-2.15.0.tgz

# Expose port for serving the Allure report
EXPOSE 1337

# Run tests with pytest and generate Allure report
CMD pytest && allure generate --clean -o allure-report allure_results && \
    echo "Allure report generated. Access it at http://localhost:1337" && \
    python -m http.server 1337 --directory allure-report