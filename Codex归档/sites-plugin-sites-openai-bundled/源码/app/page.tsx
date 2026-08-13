"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type ToolItem = {
  id: number;
  title: string;
  description: string;
  url: string;
  category: string;
  owner: string;
  kind: "link" | "tool";
  pinned?: boolean;
};

const initialItems: ToolItem[] = [
  {
    id: 1,
    title: "Sprint Board",
    description: "Engineering tasks, blockers, and release ownership.",
    url: "https://linear.app",
    category: "Delivery",
    owner: "Product Ops",
    kind: "tool",
    pinned: true,
  },
  {
    id: 2,
    title: "Design Library",
    description: "Shared components, brand assets, and Figma handoffs.",
    url: "https://figma.com",
    category: "Design",
    owner: "Design",
    kind: "link",
    pinned: true,
  },
  {
    id: 3,
    title: "Support Desk",
    description: "Customer escalations, internal requests, and SLAs.",
    url: "https://zendesk.com",
    category: "Support",
    owner: "CX",
    kind: "tool",
  },
  {
    id: 4,
    title: "Runbook Hub",
    description: "Incident playbooks, launch checklists, and approvals.",
    url: "https://notion.so",
    category: "Operations",
    owner: "Platform",
    kind: "link",
  },
];

const categories = ["All", "Delivery", "Design", "Support", "Operations"];
const storageKey = "team-portal-resources";

export default function Home() {
  const [items, setItems] = useState<ToolItem[]>(initialItems);
  const [loaded, setLoaded] = useState(false);
  const [activeCategory, setActiveCategory] = useState("All");
  const [query, setQuery] = useState("");
  const [form, setForm] = useState({
    title: "",
    url: "",
    description: "",
    category: "Delivery",
    owner: "",
    kind: "link",
  });

  const filteredItems = useMemo(() => {
    return items
      .filter((item) => {
        const categoryMatch =
          activeCategory === "All" || item.category === activeCategory;
        const text =
          `${item.title} ${item.description} ${item.owner}`.toLowerCase();
        return categoryMatch && text.includes(query.toLowerCase());
      })
      .sort((first, second) => Number(second.pinned) - Number(first.pinned));
  }, [activeCategory, items, query]);

  useEffect(() => {
    const saved = window.localStorage.getItem(storageKey);
    if (saved) {
      try {
        setItems(JSON.parse(saved));
      } catch {
        window.localStorage.removeItem(storageKey);
      }
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (loaded) {
      window.localStorage.setItem(storageKey, JSON.stringify(items));
    }
  }, [items, loaded]);

  function addItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title.trim() || !form.url.trim()) {
      return;
    }

    setItems((current) => [
      {
        id: Date.now(),
        title: form.title.trim(),
        url: form.url.trim(),
        description:
          form.description.trim() || "New team resource awaiting details.",
        category: form.category,
        owner: form.owner.trim() || "Team",
        kind: form.kind as ToolItem["kind"],
      },
      ...current,
    ]);

    setForm({
      title: "",
      url: "",
      description: "",
      category: form.category,
      owner: "",
      kind: form.kind,
    });
  }

  function togglePinned(id: number) {
    setItems((current) =>
      current.map((item) =>
        item.id === id ? { ...item, pinned: !item.pinned } : item,
      ),
    );
  }

  function removeItem(id: number) {
    setItems((current) => current.filter((item) => item.id !== id));
  }

  return (
    <main className="min-h-screen bg-[#f6f5f1] text-[#18201d]">
      <section className="border-b border-[#d9d5c9] bg-[#fffdf7]">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-7 lg:px-8">
          <header className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#557a66]">Team tools</p>
              <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">
                Team Portal
              </h1>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center">
              <Metric label="Resources" value={items.length.toString()} />
              <Metric
                label="Tools"
                value={items.filter((item) => item.kind === "tool").length.toString()}
              />
              <Metric
                label="Pinned"
                value={items.filter((item) => item.pinned).length.toString()}
              />
            </div>
          </header>

          <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
            <label className="search-wrap">
              <span>Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Find tools, links, owners..."
              />
            </label>
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <button
                  className={category === activeCategory ? "chip active" : "chip"}
                  key={category}
                  onClick={() => setActiveCategory(category)}
                  type="button"
                >
                  {category}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-6 px-5 py-6 lg:grid-cols-[1fr_360px] lg:px-8">
        <section className="space-y-4">
          <div className="section-head">
            <h2>Workspace Directory</h2>
            <span>{filteredItems.length} shown</span>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {filteredItems.map((item) => (
              <article className="tool-card" key={item.id}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`badge ${item.kind}`}>{item.kind}</span>
                      {item.pinned ? <span className="badge pinned">pinned</span> : null}
                    </div>
                    <h3>{item.title}</h3>
                  </div>
                  <div className="card-actions">
                    <button
                      aria-label={`${item.pinned ? "Unpin" : "Pin"} ${item.title}`}
                      onClick={() => togglePinned(item.id)}
                      type="button"
                    >
                      {item.pinned ? "Unpin" : "Pin"}
                    </button>
                    <a
                      aria-label={`Open ${item.title}`}
                      href={item.url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      Open
                    </a>
                  </div>
                </div>
                <p>{item.description}</p>
                <footer>
                  <span>{item.category}</span>
                  <span>{item.owner}</span>
                  <button onClick={() => removeItem(item.id)} type="button">
                    Remove
                  </button>
                </footer>
              </article>
            ))}
          </div>

          {filteredItems.length === 0 ? (
            <div className="empty-state">
              <h3>No matching resources</h3>
              <p>Add the missing link or clear the current filter.</p>
            </div>
          ) : null}
        </section>

        <aside className="add-panel">
          <div className="section-head">
            <h2>Add Resource</h2>
            <span>Live list</span>
          </div>
          <form onSubmit={addItem}>
            <label>
              Name
              <input
                value={form.title}
                onChange={(event) =>
                  setForm({ ...form, title: event.target.value })
                }
                placeholder="Analytics Console"
                required
              />
            </label>
            <label>
              URL
              <input
                value={form.url}
                onChange={(event) => setForm({ ...form, url: event.target.value })}
                placeholder="https://..."
                required
              />
            </label>
            <label>
              Description
              <textarea
                value={form.description}
                onChange={(event) =>
                  setForm({ ...form, description: event.target.value })
                }
                placeholder="What this resource is for"
                rows={4}
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              <label>
                Category
                <select
                  value={form.category}
                  onChange={(event) =>
                    setForm({ ...form, category: event.target.value })
                  }
                >
                  {categories.slice(1).map((category) => (
                    <option key={category}>{category}</option>
                  ))}
                </select>
              </label>
              <label>
                Type
                <select
                  value={form.kind}
                  onChange={(event) =>
                    setForm({ ...form, kind: event.target.value })
                  }
                >
                  <option value="link">Link</option>
                  <option value="tool">Tool</option>
                </select>
              </label>
            </div>
            <label>
              Owner
              <input
                value={form.owner}
                onChange={(event) =>
                  setForm({ ...form, owner: event.target.value })
                }
                placeholder="Team or person"
              />
            </label>
            <button className="primary-button" type="submit">
              Add to portal
            </button>
          </form>
        </aside>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
