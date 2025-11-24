import React from 'react';
import { Shield, Coins, Banknote, Skull } from 'lucide-react';

export default function PhilosophyPage() {
    return (
        <div className="container mx-auto px-4 py-12 max-w-4xl">
            <div className="text-center mb-16">
                <h1 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-orange-500 to-yellow-500 bg-clip-text text-transparent">
                    The Sovereignty Philosophy
                </h1>
                <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                    True financial sovereignty requires a balanced approach to asset allocation.
                    We categorize every asset on Algorand into four distinct buckets.
                </p>
            </div>

            <div className="space-y-12">
                {/* Hard Money */}
                <div className="bg-gray-900/50 border border-orange-500/20 rounded-2xl p-8 hover:border-orange-500/40 transition-colors">
                    <div className="flex items-start gap-6">
                        <div className="p-4 bg-orange-500/10 rounded-xl">
                            <Shield className="w-8 h-8 text-orange-500" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-orange-500 mb-4">Hard Money</h2>
                            <p className="text-gray-300 mb-4 leading-relaxed">
                                Assets that cannot be printed at will. These are your store of value, your hedge against inflation,
                                and the foundation of your sovereignty. In a world of infinite fiat currency, hard money is your anchor.
                            </p>
                            <div className="flex gap-3">
                                <span className="px-3 py-1 bg-orange-500/10 text-orange-400 rounded-full text-sm font-medium">Bitcoin (goBTC)</span>
                                <span className="px-3 py-1 bg-yellow-500/10 text-yellow-400 rounded-full text-sm font-medium">Gold (GOLD$)</span>
                                <span className="px-3 py-1 bg-gray-400/10 text-gray-300 rounded-full text-sm font-medium">Silver (SILVER$)</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Algorand */}
                <div className="bg-gray-900/50 border border-white/10 rounded-2xl p-8 hover:border-white/20 transition-colors">
                    <div className="flex items-start gap-6">
                        <div className="p-4 bg-white/5 rounded-xl">
                            <Coins className="w-8 h-8 text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white mb-4">Algorand</h2>
                            <p className="text-gray-300 mb-4 leading-relaxed">
                                The fuel of the ecosystem. ALGO is not just a currency; it's the ownership stake in the
                                most efficient, secure, and decentralized network in existence. It powers your sovereignty.
                            </p>
                            <div className="flex gap-3">
                                <span className="px-3 py-1 bg-white/10 text-white rounded-full text-sm font-medium">ALGO</span>
                                <span className="px-3 py-1 bg-white/10 text-white rounded-full text-sm font-medium">gALGO</span>
                                <span className="px-3 py-1 bg-white/10 text-white rounded-full text-sm font-medium">mALGO</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Dollars */}
                <div className="bg-gray-900/50 border border-green-500/20 rounded-2xl p-8 hover:border-green-500/40 transition-colors">
                    <div className="flex items-start gap-6">
                        <div className="p-4 bg-green-500/10 rounded-xl">
                            <Banknote className="w-8 h-8 text-green-500" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-green-500 mb-4">Dollars</h2>
                            <p className="text-gray-300 mb-4 leading-relaxed">
                                Stablecoins for payments, short-term liquidity, and hedging. While not "sovereign" in the long term
                                due to inflation, they are a necessary tool for interacting with the legacy financial system.
                            </p>
                            <div className="flex gap-3">
                                <span className="px-3 py-1 bg-green-500/10 text-green-400 rounded-full text-sm font-medium">USDC</span>
                                <span className="px-3 py-1 bg-green-500/10 text-green-400 rounded-full text-sm font-medium">USDT</span>
                                <span className="px-3 py-1 bg-green-500/10 text-green-400 rounded-full text-sm font-medium">EURS</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Shitcoins */}
                <div className="bg-gray-900/50 border border-red-500/20 rounded-2xl p-8 hover:border-red-500/40 transition-colors">
                    <div className="flex items-start gap-6">
                        <div className="p-4 bg-red-500/10 rounded-xl">
                            <Skull className="w-8 h-8 text-red-500" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-red-500 mb-4">Shitcoins</h2>
                            <p className="text-gray-300 mb-4 leading-relaxed">
                                Everything else. Speculative assets, meme coins, and unproven projects. High risk, potential high reward,
                                but fundamentally gambling. Treat them as such. Do not store your life savings here.
                            </p>
                            <div className="flex gap-3">
                                <span className="px-3 py-1 bg-red-500/10 text-red-400 rounded-full text-sm font-medium">Memecoins</span>
                                <span className="px-3 py-1 bg-red-500/10 text-red-400 rounded-full text-sm font-medium">NFTs</span>
                                <span className="px-3 py-1 bg-red-500/10 text-red-400 rounded-full text-sm font-medium">Governance Tokens</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
