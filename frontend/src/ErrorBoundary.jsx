import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    // eslint-disable-next-line no-console
    console.error('Erreur applicative interceptee :', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-fond px-6 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-2xl text-red-600">!</div>
          <p className="font-display text-2xl font-semibold text-encre">Une erreur inattendue est survenue</p>
          <p className="max-w-md text-sm text-encre-sourde">
            L'interface a rencontre un probleme. Rechargez la page pour continuer ; vos reunions restent
            sauvegardees sur le serveur.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="rounded-xl border border-bordeaux-700 bg-bordeaux-700 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-bordeaux-800"
          >
            Recharger la page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
