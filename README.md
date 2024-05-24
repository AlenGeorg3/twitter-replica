### Repository Name: 
Twitter Replica

### Description:
This repository contains a replica of Twitter (currently known as X), built as part of an assignment. The project includes basic facilities for creating and searching through tweets and users, as well as functionalities for following other users, editing and deleting tweets, and attaching images to tweets. Python FastAPI was utilized in the development process.

### Table of Contents:
1. Overview
2. Features
3. Technologies Used
4. Installation
5. Usage
6. Screenshots
7. Future Improvements
8. License

### Overview:
This project aims to replicate the core functionalities of Twitter, allowing users to create tweets, follow other users, and view timelines. Users can also edit and delete their tweets, and attach images to their tweets for richer content sharing. FastAPI, a modern web framework for building APIs with Python, was used to develop the backend.

### Features:
- **Tweet Creation:** Users can create tweets with optional image attachments in JPG or PNG format.
- **Tweet Editing and Deletion:** Users can edit and delete their tweets.
- **User Following:** Users can follow other users on the application.
- **Followers and Following List:** Users can see which users are following them and whom they are following.
- **Timeline:** Users can view a timeline of the most recent 20 tweets from the users they are following, including their own tweets, in reverse chronological order.

### Technologies Used:
- **Frontend:** HTML, CSS, JavaScript
- **Backend:** FastAPI (Python)
- **Database:** Firebase Firestore
- **Image Storage:** Google Cloud Storage Buckets

### Installation:
To set up the project locally, follow these steps:

1. Clone the repository from GitHub.
2. Navigate to the project directory.
3. Install dependencies by running `pip install -r requirements.txt`.
4. Set up Firebase and Google Cloud Platform accounts and create Firestore database and Cloud Storage buckets.
5. Configure Firebase and Google Cloud Platform credentials in the project.
6. Start the FastAPI server by running `uvicorn main:app --reload`.

### Usage:
To use the application, follow these steps:

1. Sign up for an account or log in if you already have one.
2. Create tweets by composing messages and optionally attaching images.
3. Follow other users to see their tweets on your timeline.
4. Edit or delete your tweets as needed.
5. Explore the application to discover more features!

### Screenshots:
![Screenshot 1](/screenshots/screenshot1.png)
![Screenshot 2](/screenshots/screenshot2.png)

### Future Improvements:
- Implement real-time updates for tweets and timelines using WebSocket communication.
- Enhance user authentication and authorization features.
- Improve user interface and user experience.
- Implement advanced search and filtering functionalities.

### License:
This project is licensed under the [MIT License](LICENSE).
