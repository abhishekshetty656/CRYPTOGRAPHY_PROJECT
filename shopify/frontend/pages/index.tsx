import Link from 'next/link';

export default function Home(){
  return (
    <main className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4">Multi-vendor SaaS</h1>
      <p className="mb-6">Create your store, sell products, and get paid.</p>
      <div className="space-x-4">
        <Link href="/demo/fashion" className="px-4 py-2 bg-black text-white rounded">Open Demo Store</Link>
        <Link href="/dashboard" className="px-4 py-2 border rounded">Merchant Dashboard</Link>
      </div>
    </main>
  )
}
