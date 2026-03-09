import { GetServerSideProps } from 'next';
import Link from 'next/link';

export default function StorePage({ store, products }: any){
  return (
    <main className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-semibold">{store.name}</h1>
      <p className="text-gray-600 mb-4">{store.description || 'Welcome to our store'}</p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {products.map((p: any) => (
          <Link key={p.id} href={`/${store.subdomain}/${p.slug}`} className="border rounded p-3">
            <div className="font-medium">{p.title}</div>
            <div className="text-sm">${(p.priceCents/100).toFixed(2)}</div>
          </Link>
        ))}
      </div>
    </main>
  );
}

export const getServerSideProps: GetServerSideProps = async ({ params }) => {
  const subdomain = params?.store as string;
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
  const sres = await fetch(`${API}/api/stores/${subdomain}`);
  if (!sres.ok) return { notFound: true };
  const store = await sres.json();
  const pres = await fetch(`${API}/api/products/by-store/${store.id}`);
  const products = await pres.json();
  return { props: { store, products } };
}
