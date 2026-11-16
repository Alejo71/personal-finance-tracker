import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const money = (value) => new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value || 0);

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Algo salió mal");
  return body;
}

function Auth({ onLogin }) {
  const [registering, setRegistering] = useState(false);
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      if (registering) await request("/auth/register", { method: "POST", body: JSON.stringify(form) });
      const data = await request("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams(form),
      });
      localStorage.setItem("token", data.access_token);
      onLogin(data.access_token);
    } catch (err) {
      setError(err.message);
    }
  };

  return <main className="auth-page">
    <section className="auth-card">
      <div className="brand-mark">₱</div>
      <p className="eyebrow">MIS FINANZAS</p>
      <h1>Tu dinero, más claro.</h1>
      <p className="muted">Lleva el control de tus gastos sin complicarte.</p>
      <form onSubmit={submit}>
        <label>Usuario<input required minLength="3" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></label>
        <label>Contraseña<input required minLength="6" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
        {error && <p className="error">{error}</p>}
        <button>{registering ? "Crear cuenta" : "Entrar"}</button>
      </form>
      <button className="link-button" onClick={() => setRegistering(!registering)}>
        {registering ? "Ya tengo una cuenta" : "Soy nuevo, quiero registrarme"}
      </button>
    </section>
  </main>;
}

function Dashboard({ token, onLogout }) {
  const headers = { Authorization: `Bearer ${token}` };
  const [data, setData] = useState({ summary: {}, wallets: [], categories: [], transactions: [] });
  const [form, setForm] = useState({ wallet_id: "", category_id: "", amount: "", transaction_type: "expense", payment_method: "" });
  const [newWallet, setNewWallet] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [summary, wallets, categories, transactions] = await Promise.all([
        request("/summary", { headers }), request("/wallets", { headers }),
        request("/categories", { headers }), request("/transactions", { headers }),
      ]);
      setData({ summary, wallets, categories, transactions });
      if (!form.wallet_id && wallets[0]) setForm((current) => ({ ...current, wallet_id: wallets[0].wallet_id }));
      if (!form.category_id && categories[0]) setForm((current) => ({ ...current, category_id: categories[0].category_id }));
    } catch (err) { setError(err.message); }
  };

  useEffect(() => { load(); }, []);

  const addWallet = async () => {
    if (!newWallet.trim()) return;
    await request("/wallets", { method: "POST", headers, body: JSON.stringify({ name: newWallet, balance: 0 }) });
    setNewWallet("");
    load();
  };

  const addTransaction = async (event) => {
    event.preventDefault();
    try {
      await request("/transactions", { method: "POST", headers, body: JSON.stringify({
        ...form, wallet_id: Number(form.wallet_id), category_id: Number(form.category_id), amount: Number(form.amount),
      }) });
      setForm({ ...form, amount: "" });
      load();
    } catch (err) { setError(err.message); }
  };

  return <main className="app-shell">
    <header className="topbar"><div><p className="eyebrow">MIS FINANZAS</p><h2>Hola, ¿cómo va tu día?</h2></div><button className="logout" onClick={onLogout}>Salir</button></header>
    {error && <p className="error">{error}</p>}
    <section className="summary-grid">
      <article className="summary-card main"><span>Balance total</span><strong>{money(data.summary.balance)}</strong><small>Lo que tienes disponible</small></article>
      <article className="summary-card"><span>Ingresos</span><strong className="green">{money(data.summary.income)}</strong><small>Este periodo</small></article>
      <article className="summary-card"><span>Gastos</span><strong className="red">{money(data.summary.expenses)}</strong><small>Este periodo</small></article>
    </section>
    <section className="content-grid">
      <div className="panel"><div className="panel-title"><h3>Agregar movimiento</h3><span>+</span></div>
        <form className="movement-form" onSubmit={addTransaction}>
          <label>Tipo<select value={form.transaction_type} onChange={(e) => setForm({ ...form, transaction_type: e.target.value })}><option value="expense">Gasto</option><option value="income">Ingreso</option></select></label>
          <label>Valor<input required type="number" min="1" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></label>
          <label>Billetera<select required value={form.wallet_id} onChange={(e) => setForm({ ...form, wallet_id: e.target.value })}>{data.wallets.map((w) => <option key={w.wallet_id} value={w.wallet_id}>{w.name}</option>)}</select></label>
          <label>Categoría<select required value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>{data.categories.map((c) => <option key={c.category_id} value={c.category_id}>{c.category_name}</option>)}</select></label>
          <button>Guardar movimiento</button>
        </form>
      </div>
      <div className="panel"><div className="panel-title"><h3>Mis billeteras</h3></div>
        {data.wallets.map((wallet) => <div className="wallet" key={wallet.wallet_id}><span className="wallet-icon">◈</span><div><b>{wallet.name}</b><small>Saldo actual</small></div><strong>{money(wallet.balance)}</strong></div>)}
        <div className="add-wallet"><input placeholder="Nueva billetera" value={newWallet} onChange={(e) => setNewWallet(e.target.value)} /><button onClick={addWallet}>Añadir</button></div>
      </div>
    </section>
    <section className="panel history"><div className="panel-title"><h3>Movimientos recientes</h3></div>
      {data.transactions.length === 0 ? <p className="muted">Todavía no tienes movimientos. ¡Agrega el primero!</p> : data.transactions.map((item) => {
        const category = data.categories.find((c) => c.category_id === item.category_id);
        return <div className="transaction" key={item.transaction_id}><span className={item.transaction_type === "income" ? "dot green-bg" : "dot red-bg"}></span><div><b>{category?.category_name || "Movimiento"}</b><small>{new Date(item.created_at).toLocaleDateString("es-CO")}</small></div><strong className={item.transaction_type === "income" ? "green" : "red"}>{item.transaction_type === "income" ? "+" : "-"}{money(item.amount)}</strong></div>;
      })}
    </section>
  </main>;
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  return token ? <Dashboard token={token} onLogout={() => { localStorage.removeItem("token"); setToken(null); }} /> : <Auth onLogin={setToken} />;
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
