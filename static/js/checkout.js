(function () {
    const cepInput = document.querySelector("#id_shipping_postal_code");
    const searchButton = document.querySelector("#cep-search");
    const status = document.querySelector("#cep-status");
    if (!cepInput || !searchButton || !status) return;

    const fields = {
        address: document.querySelector("#id_shipping_address"),
        neighborhood: document.querySelector("#id_shipping_neighborhood"),
        city: document.querySelector("#id_shipping_city"),
        state: document.querySelector("#id_shipping_state"),
    };

    function cleanCep(value) {
        return value.replace(/\D/g, "").slice(0, 8);
    }

    function setStatus(message, kind) {
        status.textContent = message;
        status.dataset.state = kind || "";
    }

    async function searchCep() {
        const cep = cleanCep(cepInput.value);
        if (cep.length !== 8) {
            setStatus("Digite um CEP válido com 8 números.", "error");
            return;
        }

        searchButton.disabled = true;
        setStatus("Buscando endereço…", "loading");
        try {
            const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`, {
                headers: { Accept: "application/json" },
            });
            if (!response.ok) throw new Error("request-failed");
            const data = await response.json();
            if (data.erro) throw new Error("not-found");
            fields.address.value = data.logradouro || "";
            fields.neighborhood.value = data.bairro || "";
            fields.city.value = data.localidade || "";
            fields.state.value = data.uf || "";
            setStatus("Endereço preenchido. Confira e informe o número.", "success");
            document.querySelector("#id_shipping_number").focus();
        } catch (error) {
            setStatus("Não encontramos esse CEP. Você pode preencher o endereço manualmente.", "error");
        } finally {
            searchButton.disabled = false;
        }
    }

    cepInput.addEventListener("input", () => {
        const cep = cleanCep(cepInput.value);
        cepInput.value = cep.length > 5 ? `${cep.slice(0, 5)}-${cep.slice(5)}` : cep;
        if (cep.length < 8) setStatus("", "");
        if (cep.length === 8) searchCep();
    });
    cepInput.addEventListener("blur", searchCep);
    searchButton.addEventListener("click", searchCep);
})();

(function () {
    const form = document.querySelector(".store-app .checkout-form");
    if (!form) return;
    const button = form.querySelector('button[type="submit"]');
    if (!button) return;
    form.addEventListener("submit", () => {
        button.disabled = true;
        button.setAttribute("aria-busy", "true");
    });
    window.addEventListener("pageshow", () => {
        button.disabled = false;
        button.removeAttribute("aria-busy");
    });
})();
