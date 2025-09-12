import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'F1 Undercut Simulator',
  description: 'Advanced Formula 1 undercut strategy simulation and analysis tool',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
          <header className="f1-gradient shadow-lg">
            <div className="container mx-auto px-4 py-6">
              <h1 className="text-3xl font-bold text-white">
                🏎️ F1 Undercut Simulator
              </h1>
              <p className="text-red-100 mt-2">
                Advanced Formula 1 undercut strategy simulation and analysis
              </p>
            </div>
          </header>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
