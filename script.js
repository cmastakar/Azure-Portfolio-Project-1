const form = document.getElementById("contactForm");
const formMessage = document.getElementById("formMessage");

form.addEventListener("submit", async function (event) {
  event.preventDefault();

  formMessage.textContent = "Sending...";

  const turnstileToken =
    document.querySelector('[name="cf-turnstile-response"]')?.value;

  if (!turnstileToken) {
    formMessage.textContent =
      "Please complete the security verification.";
    return;
  }

  const formData = {
    name: document.getElementById("name").value.trim(),
    email: document.getElementById("email").value.trim(),
    company: document.getElementById("company").value.trim(),
    message: document.getElementById("message").value.trim(),
    website: document.getElementById("website")?.value.trim() || "",
    turnstileToken: turnstileToken
  };

  try {
    const response = await fetch(
      "https://chandanportfolioapi-bqbngybbb4hrgtdr.westus3-01.azurewebsites.net/api/contact",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      }
    );

    const result = await response.json();

    if (response.ok) {
      formMessage.textContent =
        result.message || "Message sent successfully.";

      form.reset();

      if (typeof turnstile !== "undefined") {
        turnstile.reset();
      }
    } else {
      formMessage.textContent =
        result.error || "Something went wrong.";
    }

  } catch (error) {
    console.error(error);

    formMessage.textContent =
      "Unable to send message. Please try again.";
  }
});

function openNav() {
  document.getElementById("mySidenav").style.width = "250px";
}

function closeNav() {
  document.getElementById("mySidenav").style.width = "0";
}
