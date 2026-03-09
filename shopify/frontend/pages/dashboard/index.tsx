import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export default function MerchantDashboard(){
  const [token, setToken] = useState('');
  const [stores, setStores] = useState<any[]>([]);
  const [name, setName] = useState('');
  const [subdomain, setSubdomain] = useState('');

  useEffect(()=>{
    const t = localStorage.getItem('token')||''; setToken(t);
    if (t) fetch(`${API}/api/stores/mine`, { headers: { Authorization: `Bearer ${t}`}}).then(r=>r.json()).then(setStores);
  },[]);

  const create = async ()=>{
    const r = await fetch(`${API}/api/stores`, { method: 'POST', headers: { 'Content-Type':'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ name, subdomain }) });
    const s = await r.json();
    setStores(prev=>[...prev, s]);
  }

  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-4">Merchant Dashboard</h1>
      {!token && <Auth setToken={setToken} />}
      {token && (
        <>
          <div className="mb-6">
            <h2 className="font-medium mb-2">Create Store</h2>
            <div className="flex gap-2">
              <input className="border px-2 py-1" placeholder="Name" value={name} onChange={e=>setName(e.target.value)} />
              <input className="border px-2 py-1" placeholder="subdomain" value={subdomain} onChange={e=>setSubdomain(e.target.value)} />
              <button className="px-3 py-1 bg-black text-white" onClick={create}>Create</button>
            </div>
          </div>
          <div>
            <h2 className="font-medium mb-2">Your Stores</h2>
            <ul className="list-disc pl-6">
              {stores.map(s=> <li key={s.id}>{s.name} — <a className="text-blue-600" href={`/${s.subdomain}`}>/{s.subdomain}</a></li>)}
            </ul>
          </div>
        </>
      )}
    </main>
  )
}

function Auth({ setToken }: any){
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const signup = async ()=>{
    const r = await fetch(`${API}/api/auth/signup`, { method: 'POST', headers: { 'Content-Type': 'application/json'}, body: JSON.stringify({ email, password }) });
    const d = await r.json(); localStorage.setItem('token', d.token); setToken(d.token);
  }
  const login = async ()=>{
    const r = await fetch(`${API}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json'}, body: JSON.stringify({ email, password }) });
    const d = await r.json(); localStorage.setItem('token', d.token); setToken(d.token);
  }

  return (
    <div className="mb-6">
      <h2 className="font-medium mb-2">Login / Signup</h2>
      <div className="flex gap-2">
        <input className="border px-2 py-1" placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="border px-2 py-1" placeholder="password" value={password} type="password" onChange={e=>setPassword(e.target.value)} />
        <button className="px-3 py-1 bg-black text-white" onClick={login}>Login</button>
        <button className="px-3 py-1 border" onClick={signup}>Signup</button>
      </div>
    </div>
  )
}
