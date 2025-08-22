# Calibration Tool

This is a web application designed to help engineering managers and leads conduct performance calibrations. Managers can input comments about their direct reports based on behaviors and results. The tool provides a dashboard to visualize employee performance and uses the OpenAI API to analyze comment sentiment and classify performance levels.

## Features

- **Role-Based Access Control:**
  - **Engineering Lead:** Can view all calibration data across all teams.
  - **Manager:** Can only view and manage data for their direct reports.
- **9-Box Performance Grid:** A visual dashboard to plot employees based on their performance and behavior, providing an at-a-glance view of the team's calibration.
- **AI-Powered Analysis:** Integrates with the OpenAI API to automatically assess the sentiment of calibration comments and classify them as 'Developing', 'Achieving', or 'Exceeding'.
- **Mock Data:** Comes with a pre-populated database to allow for easy visualization and testing of the application's features.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    - Rename the `.env.example` file to `.env`.
    - Open the `.env` file and add your OpenAI API key:
      ```
      OPENAI_API_KEY=your_openai_api_key_here
      ```

5.  **Create and populate the database:**
    - The application is configured to use SQLite. The first time you run the app, it will create the database file. To populate it with mock data, you can temporarily uncomment the `create_mock_data()` call in `app.py`.

6.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will be available at `http://127.0.0.1:5000`.

## Future Extensions

This application is built to be extensible. Here are some potential features that could be added in the future:

- **Historical Performance Tracking:** Implement a system to view an employee's calibration data over time, allowing for tracking of progress and growth.
- **Direct Employee Feedback:** Add a feature for employees to view their feedback and add their own comments or self-assessments.
- **HRIS Integration:** Integrate with HRIS platforms (like Workday or BambooHR) to automatically sync employee and manager data.
- **Advanced Analytics:** Introduce more sophisticated analytics and reporting features, such as team-wide performance trends and comparison charts.
- **Customizable Frameworks:** Allow companies to define their own performance frameworks and classification labels beyond the default 'Developing', 'Achieving', 'Exceeding'.
- **Notifications:** Add email or in-app notifications to remind managers about upcoming calibration cycles.
