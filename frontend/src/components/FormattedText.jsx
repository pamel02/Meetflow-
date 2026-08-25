// Les reponses generees par le LLM utilisent parfois une syntaxe Markdown
// legere (**gras**). Ce composant l'interprete pour un rendu propre, sans
// jamais afficher les asterisques bruts a l'utilisateur.

function renderBoldSegments(line, keyPrefix) {
  const parts = [];
  const regex = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match;
  let i = 0;

  while ((match = regex.exec(line)) !== null) {
    if (match.index > lastIndex) {
      parts.push(<span key={`${keyPrefix}-${i++}`}>{line.slice(lastIndex, match.index)}</span>);
    }
    parts.push(
      <strong key={`${keyPrefix}-${i++}`} className="font-semibold text-encre">
        {match[1]}
      </strong>
    );
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < line.length) {
    parts.push(<span key={`${keyPrefix}-${i++}`}>{line.slice(lastIndex)}</span>);
  }
  return parts;
}

export default function FormattedText({ text }) {
  if (!text) return null;
  const lines = String(text).split('\n');
  return (
    <>
      {lines.map((line, li) => (
        <span key={li}>
          {renderBoldSegments(line, li)}
          {li < lines.length - 1 && <br />}
        </span>
      ))}
    </>
  );
}