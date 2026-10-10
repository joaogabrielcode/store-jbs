const menuToggle = document.querySelector("[data-menu-toggle]");
const navigation = document.querySelector("[data-nav]");
const cartDrawer = document.querySelector("[data-cart-drawer]");
const cartBackdrop = document.querySelector(".cart-drawer-backdrop");
const cartContent = document.querySelector("[data-cart-content]");
const cartToggles = document.querySelectorAll("[data-cart-toggle]");
const cartCloseButtons = document.querySelectorAll("[data-cart-close]");
const cartPeek = document.querySelector("[data-cart-peek]");
const canHoverCart = window.matchMedia("(hover: hover)").matches;
let cartCloseTimer;

const setCartDrawerState = (isOpen) => {
    if (!cartDrawer) return;
    window.clearTimeout(cartCloseTimer);

    if (isOpen) {
        cartDrawer.hidden = false;
        cartDrawer.style.display = "flex";
        if (cartBackdrop) {
            cartBackdrop.hidden = false;
            cartBackdrop.style.display = "block";
        }
        window.requestAnimationFrame(() => {
            cartDrawer.classList.add("is-open");
            cartBackdrop?.classList.add("is-open");
        });
    } else {
        cartDrawer.classList.remove("is-open");
        cartBackdrop?.classList.remove("is-open");
        cartCloseTimer = window.setTimeout(() => {
            if (cartDrawer.classList.contains("is-open")) return;
            cartDrawer.hidden = true;
            cartDrawer.style.display = "none";
            if (cartBackdrop) {
                cartBackdrop.hidden = true;
                cartBackdrop.style.display = "none";
            }
        }, 240);
    }

    if (cartPeek) {
        cartPeek.hidden = isOpen;
        cartPeek.style.display = isOpen ? "none" : "grid";
    }
    cartDrawer.setAttribute("aria-hidden", String(!isOpen));
    document.body.classList.toggle("cart-drawer-open", isOpen);
    cartToggles.forEach((toggle) => toggle.setAttribute("aria-expanded", String(isOpen)));
};

const openCartDrawer = () => {
    window.clearTimeout(cartCloseTimer);
    setCartDrawerState(true);
};

const scheduleCartDrawerClose = () => {
    if (!canHoverCart) return;
    window.clearTimeout(cartCloseTimer);
    cartCloseTimer = window.setTimeout(() => setCartDrawerState(false), 180);
};

cartToggles.forEach((toggle) => {
    toggle.setAttribute("aria-expanded", "false");
    toggle.addEventListener("click", (event) => {
        event.preventDefault();
        openCartDrawer();
    });
});

if (cartPeek) {
    cartPeek.addEventListener("click", openCartDrawer);
    cartPeek.addEventListener("mouseenter", openCartDrawer);
}

if (canHoverCart && cartDrawer) {
    cartDrawer.addEventListener("mouseenter", openCartDrawer);
    cartDrawer.addEventListener("mouseleave", scheduleCartDrawerClose);
}

document.addEventListener("click", (event) => {
    const navigationLink = event.target.closest("[data-cart-navigate]");
    if (navigationLink) {
        event.preventDefault();
        const destination = navigationLink.href;
        setCartDrawerState(false);
        window.setTimeout(() => window.location.assign(destination), 240);
        return;
    }
    if (event.target.closest("[data-cart-close], [data-cart-collapse]")) {
        setCartDrawerState(false);
    }
});

cartCloseButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        setCartDrawerState(false);
    });
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setCartDrawerState(false);
});

const updateCartDrawer = (data) => {
    if (cartContent) cartContent.innerHTML = data.html;
    document.querySelectorAll(".cart-link b").forEach((badge) => {
        badge.textContent = data.cart_count;
    });
    openCartDrawer();
};

document.querySelectorAll("[data-cart-add]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
        if (event.submitter?.hasAttribute("data-buy-now")) return;
        event.preventDefault();
        const button = event.submitter || form.querySelector("button[type='submit']");
        if (button) button.disabled = true;
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    Accept: "application/json",
                },
            });
            if (!response.ok) throw new Error("Não foi possível adicionar o produto.");
            updateCartDrawer(await response.json());
        } catch (error) {
            form.submit();
        } finally {
            if (button) button.disabled = false;
        }
    });
});

if (menuToggle && navigation) {
    menuToggle.addEventListener("click", () => {
        const isOpen = document.body.classList.toggle("menu-open");
        menuToggle.setAttribute("aria-expanded", String(isOpen));
        navigation.classList.toggle("is-open", isOpen);
    });

    navigation.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            document.body.classList.remove("menu-open");
            navigation.classList.remove("is-open");
            menuToggle.setAttribute("aria-expanded", "false");
        });
    });
}
