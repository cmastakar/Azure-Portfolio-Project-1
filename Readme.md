Azure Portfolio Project #1 : Serverless Azure Portfolio Website 

URL: https://wonderful-bay-05fbbb710.7.azurestaticapps.net

Overview 
This project is a simple portfolio website hosted on Azure Static Web Appsused to showcase my experiences and hands on Cloud projects. The website contains a simple contact form and email delivery features. 

Architecture
The hierarchy of architecture used to create this project is as follows:
Visitor to website-> Azure Static Web Apps -> HTML/CSS/JS->Cloudflare token generated-> JS sends form & token-> Azure Function -> Cloudflare token verification -> Azure Communication Services Email  

Operational Architecture 
User/Visitor to website -> Static Web App -> HTML/CSS/JS -> Cloudflare Validation-> Azure Function (Validation input / Honeypot Check / Verification of Turnstile/ Read Azure env variable secrets)
->Creates Azure communication services email from User input -> Email delivered to account specified in Azure 

Azure Services Used
Static Web Apps, Functions, Communication Services, Email Communication Services, Microsoft Entra ID , RBAC 

Other External Technologies 
GitHub, GitHub actions, Cloudflare Turnstile, Python, Javascript, HTML, CSS 

Security Implemented
CORS, server-side Validation, honeypot, Turnstile, Environment variables/secrets, Anonymous endpoint design
The project makes use of defense in depth, by implementing several layers of security to ensure maximum effectivity and protection. Values which may pose security issues if exposed(Such as Turnstile secrets and Azure communciation Services connection strings) have been placed in the Back end, to prevent front end exposure.

CI/CD 
The deployment is handled by GitHub, and changes pushed to the GitHub main branch are deployed automatically to Azure Static Web Apps.  The GitHub repository is organized in such a way that the function and HTML/CSS/JS 
are deployed to different services. 

Learning Experiences
Deploying websites with Azure Static Web Apps 
Building serverless APIs with Azure functions
Configuring GitHub actions CI/CD
Authenticating GitHub using OIDC
Using MS Entra ID and RBAC
Managing secrets and environment variables 
Understanding CORS
Implementing bot verification 
Integrating Azure Communication Services Email 
Troubleshooting Deployment and Errors

Troubleshooting 
CORS Configuration
Cloudflare Turnstile verification failures
HTTP 400, 403 and 502 error response handling 
