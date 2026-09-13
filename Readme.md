Azure Portfolio Project #1 : Serverless Azure Portfolio Website 

URL: https://wonderful-bay-05fbbb710.7.azurestaticapps.net

Overview 
This project is a simple portfolio website hosted on Azure static apps used to showcase my experiences and hands on Cloud projects. The website contains a simple contact form and email delivery features. 

Architecture
The hierarchy of architecture used to create this project is as follows:
HTML/FrontEnd ->Static Web App -> JavaScript -> Azure Function -> Turnstile -> ACS Email 

I initially started off the project by developing a simple outline or draft of the front end customer facing elements of the project such as the: website, visual content and the text content that would go into the site. This involved the creation of the Main and Contact pages, as well as ensuring the correct contact details were listed/available through the aforementioned pages. 

The back end development started in Azure where I set up a basic static web app which would serve as the basis of my portfolio website. 


Azure Services Used
Static Web Apps, Functions, Communication Services, Email Communication Services, managed Domain

Security Implemented
CORS, server-side Validation, honeypot, Turnstile, Environment vairables/secretes, Anonymous endpoint design 

CI/CD 
GITHUB actions, Separated frontend and backend deployments 

