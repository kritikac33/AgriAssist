import { useCallback, useEffect, useState } from 'react';
import { buyerAPI } from '../api/buyer';
import { marketplaceAPI, type Message } from '../api/marketplace';
import { useAuth } from '../contexts/AuthContext';
import { formatError } from '../utils/errorFormatter';

export default function BuyerMessages() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<any[]>([]);
  const [active, setActive] = useState<any | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const loadConversations = useCallback(async () => setConversations(await buyerAPI.conversations()), []);
  const loadMessages = useCallback(async (listingId: number) => setMessages(await marketplaceAPI.getMessages(listingId)), []);
  useEffect(() => { loadConversations().catch((e) => setError(formatError(e))); }, [loadConversations]);
  useEffect(() => {
    if (!active) return;
    loadMessages(active.listing_id).then(loadConversations).catch((e) => setError(formatError(e)));
    const timer = window.setInterval(() => { loadMessages(active.listing_id).then(loadConversations).catch(() => {}); }, 15000);
    return () => window.clearInterval(timer);
  }, [active, loadMessages, loadConversations]);
  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!active || !draft.trim()) return;
    try { await marketplaceAPI.sendMessage(active.listing_id, draft.trim()); setDraft(''); await loadMessages(active.listing_id); await loadConversations(); }
    catch (e) { setError(formatError(e)); }
  };
  return <div className="space-y-5"><div><h1 className="text-3xl font-bold">Messages</h1><p className="text-gray-600">Conversations about marketplace listings. Messages refresh automatically.</p></div>{error && <p role="alert" className="rounded bg-red-50 p-3 text-red-800">{error}</p>}<div className="grid min-h-[60vh] gap-4 lg:grid-cols-[320px_1fr]"><aside className="rounded-lg border bg-white p-3"><h2 className="mb-3 font-semibold">Farmer conversations</h2>{!conversations.length ? <p className="p-3 text-sm text-gray-600">No conversations yet. Contact a farmer from a listing.</p> : conversations.map((thread) => <button key={thread.listing_id} onClick={() => setActive(thread)} className={`mb-2 w-full rounded border p-3 text-left ${active?.listing_id === thread.listing_id ? 'border-primary-500 bg-green-50' : ''}`}><span className="flex items-center justify-between gap-2 font-medium">{thread.seller_name}{thread.unread_count > 0 && <span className="rounded-full bg-primary-600 px-2 py-0.5 text-xs text-white">{thread.unread_count} new</span>}</span><span className="block text-sm">{thread.crop_name}</span><span className="block truncate text-xs text-gray-500">{thread.last_message}</span><span className="text-xs text-gray-400">{new Date(thread.last_message_at).toLocaleString()}</span></button>)}</aside><section className="flex min-h-[420px] flex-col rounded-lg border bg-white p-4"><h2 className="border-b pb-3 font-semibold">{active ? `${active.crop_name} · ${active.seller_name}` : 'Select a conversation'}</h2>{active ? <><div className="flex-1 space-y-3 overflow-y-auto py-4">{messages.map((message) => <div key={message.id} className={`max-w-[85%] rounded-lg p-3 ${message.sender_id === user?.id ? 'ml-auto bg-green-100' : 'bg-gray-100'}`}><p className="text-xs text-gray-500">{message.sender_id === user?.id ? 'You' : message.sender_name || active.seller_name} · {new Date(message.created_at).toLocaleString()}</p><p>{message.content}</p></div>)}</div><form onSubmit={send} className="flex gap-2 border-t pt-3"><label className="sr-only" htmlFor="buyer-message">Message farmer</label><input id="buyer-message" value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={5000} className="min-w-0 flex-1 rounded border px-3 py-2" placeholder="Write a message…" /><button disabled={!draft.trim()} className="rounded bg-primary-600 px-4 py-2 text-white disabled:opacity-50">Send</button></form></> : <p className="m-auto text-gray-500">Choose a conversation to read and reply.</p>}</section></div></div>;
}
