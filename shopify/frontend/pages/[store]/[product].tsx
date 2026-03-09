import { GetServerSideProps } from 'next';
import { useDispatch } from 'react-redux';
import { addItem } from '@/store/slices/cart';

export default function ProductPage({ store, product }: any){
  const dispatch = useDispatch();
  return (
    <main className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-2">{product.title}</h1>
      <p className="text-gray-700 mb-4">{product.description}</p>
      <div className="mb-6">${(product.priceCents/100).toFixed(2)}</div>
      <button className="px-4 py-2 bg-black text-white rounded" onClick={()=>dispatch(addItem({ id: product.id, title: product.title, priceCents: product.priceCents, quantity: 1 }))}>Add to cart</button>
    </main>
  );
}

export const getServerSideProps: GetServerSideProps = async ({ params }) => {
  const subdomain = params?.store as string;
  const slug = params?.product as string;
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
  const sres = await fetch(`${API}/api/stores/${subdomain}`);
  if (!sres.ok) return { notFound: true };
  const store = await sres.json();
  const pres = await fetch(`${API}/api/products/by-store/${store.id}`);
  const products = await pres.json();
  const product = products.find((p: any)=> p.slug === slug);
  if (!product) return { notFound: true };
  return { props: { store, product } };
}
