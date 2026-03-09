import useSWR from 'swr';
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
const fetcher = (url: string) => fetch(url, { headers: { Authorization: '' } }).then(r=>r.json());

export default function AdminHome(){
  const { data } = useSWR(`${API}/api/admin/stats`, fetcher);
  return (
    <main className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-4">Platform Analytics</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 border rounded"><div className="text-gray-500">Stores</div><div className="text-2xl">{data?.stores ?? '...'}</div></div>
        <div className="p-4 border rounded"><div className="text-gray-500">Users</div><div className="text-2xl">{data?.users ?? '...'}</div></div>
        <div className="p-4 border rounded"><div className="text-gray-500">Revenue</div><div className="text-2xl">${((data?.platformRevenueCents ?? 0)/100).toFixed(2)}</div></div>
      </div>
    </main>
  );
}
