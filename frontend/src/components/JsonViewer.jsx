function JsonViewer({ data }) {
  const jsonString = JSON.stringify(data, null, 2)

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg p-6">
      <div className="bg-slate-900 rounded-lg overflow-auto max-h-[70vh]">
        <pre className="p-6 text-sm leading-relaxed text-slate-300 font-mono">
          <code className="text-cyan-400">{jsonString}</code>
        </pre>
      </div>
    </div>
  )
}

export default JsonViewer
