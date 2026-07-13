var backend_url = window.location.origin;
function hide_feedback(domain) {
    return `<div><small>Domínio <a href="https://${domain}">${domain}</a> escondido. | <button class="show">exibir</button></small></div>`;
}

function report_feedback(li) {
    li.style.opacity = 0.5;
    const btn = li.querySelector("button.report");
    btn.textContent = "reportado";
    btn.className = "unreport";
}

var reported = localStorage.getItem('reported') || '[]';
reported = JSON.parse(reported);
var hidden = localStorage.getItem('hidden') || '[]';
hidden = JSON.parse(hidden);

let domains = Array.from(document.getElementsByClassName("domain"));
domains.forEach((domain) => {
    if (reported.includes(domain.textContent)) {
        const li = domain.closest("li");
        report_feedback(li);
    }
    if (hidden.includes(domain.textContent)) {
        domain.closest("li").innerHTML = hide_feedback(domain.textContent);
    }
});

function report(btn) {
    const li = btn.closest("li");
    const articleDomain = li.querySelector("a.domain");
    const domain = articleDomain.textContent;

    if (reported.length == 0) {
        const agreed = confirm("Reporte sites que não são blogs pessoais ou não estão em português. Confirme para não ver mais essa mensagem. Obrigado!");
        if (!agreed) {
            return;
        }
    }
    fetch(`${backend_url}/report`, {
        method: "POST",
        body: JSON.stringify({ domain }),
        headers: {
            "Content-Type": "application/json"
        }
    });
    reported.push(domain);
    localStorage.setItem('reported', JSON.stringify(reported));
    report_feedback(li);
}

function unreport(btn) {
    const li = btn.closest("li");
    const articleDomain = li.querySelector("a.domain");
    const domain = articleDomain.textContent;
    reported = reported.filter((d) => d != domain);
    localStorage.setItem('reported', JSON.stringify(reported));
    fetch(`${backend_url}/report`, {
        method: "POST",
        body: JSON.stringify({ domain }),
        headers: {
            "Content-Type": "application/json"
        }
    }).finally(() => {
        window.location.reload();
    });
}

function hide(btn) {
    const li = btn.closest("li");
    const articleDomain = li.querySelector("a.domain");
    const domain = articleDomain.textContent;

    hidden.push(domain);
    localStorage.setItem('hidden', JSON.stringify(hidden));
    li.innerHTML = hide_feedback(domain);
}

function show(btn) {
    const li = btn.closest("li");
    const articleDomain = li.querySelector("a");
    const domain = articleDomain.textContent;
    hidden = hidden.filter((d) => d != domain);
    localStorage.setItem('hidden', JSON.stringify(hidden));
    window.location.reload();
}

document.addEventListener("click", function(e) {
    if (e.target.className == "report") {
        return report(e.target);
    }
    if (e.target.className == "unreport") {
        return unreport(e.target);
    }
    if (e.target.className == "hide") {
        return hide(e.target);
    }
    if (e.target.className == "show") {
        return show(e.target);
    }
});
