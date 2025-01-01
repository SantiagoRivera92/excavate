# Excavate Project

Welcome to the Excavate project! This project is hosted at [https://www.excavate.top](https://www.excavate.top).

Note that this does not include the MongoDB database. You will have to figure that one out yourself. If you want to contribute to the project, shoot me an e-mail and we can figure it out.

## Overview

Excavate is a web application designed to help users search for and explore Yu-Gi-Oh! cards. It provides various features including card search, random card display, syntax guide, and a golf game to match cards with the shortest query.

## Features

- **Card Search**: Search for Yu-Gi-Oh! cards using various filters and queries.
- **Random Card**: Display a random Yu-Gi-Oh! card.
- **Syntax Guide**: Learn how to use the search syntax effectively.
- **Golf Game**: Challenge yourself to match cards with the shortest query without using "or".

## Installation

To run the project locally, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/SantiagoRivera/excavate.git
    ```
2. Navigate to the project directory:
    ```bash
    cd excavate
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Set up the configuration file:
    - Create a `config/config.json` file with the following content:
    ```json
    {
        "mongo_uri": "your_mongo_uri",
        "static_version": "1.0.0",
        "staging": false
    }
    ```
    - Replace `your_mongo_uri` with your actual MongoDB URI.

5. Run the application:
    ```bash
    python src/app.py
    ```

## Usage

Once the application is running, you can access it in your web browser at `http://localhost:5000`.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please contact the project maintainer at [santirivera92@gmail.com](mailto:santirivera92@gmail.com).

Enjoy using Excavate!
