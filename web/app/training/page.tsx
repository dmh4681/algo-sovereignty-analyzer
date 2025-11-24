'use client'

import { useState, useEffect } from 'react'
import { useWallet } from '@txnlab/use-wallet-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2, Lock, Unlock, Brain, Shield, Zap } from 'lucide-react'
import algosdk from 'algosdk'
import ReactMarkdown from 'react-markdown'

export default function TrainingPage() {
    const { activeAccount, signTransactions } = useWallet()
    const [isUnlocked, setIsUnlocked] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [analysis, setAnalysis] = useState<any>(null)
    const [advice, setAdvice] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    // Use a reliable Algod node (AlgoNode) explicitly
    const algodClient = new algosdk.Algodv2('', 'https://mainnet-api.algonode.cloud', '')

    // Load analysis from local storage or fetch (mocked for now by checking URL param or just using last analysis)
    useEffect(() => {
        // In a real app, we'd use a context or store. For now, we'll try to fetch if we have an address
        if (activeAccount) {
            fetchAnalysis(activeAccount.address)
        }
    }, [activeAccount])

    const fetchAnalysis = async (address: string) => {
        try {
            const res = await fetch(`http://localhost:8000/api/v1/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address })
            })
            if (res.ok) {
                const data = await res.json()
                setAnalysis(data)
            }
        } catch (e) {
            console.error("Failed to fetch analysis", e)
        }
    }

    const fetchAdvice = async (analysisData: any) => {
        try {
            const res = await fetch(`http://localhost:8000/api/v1/agent/advice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address: activeAccount?.address || '',
                    analysis: analysisData
                })
            })
            if (res.ok) {
                const data = await res.json()
                setAdvice(data.advice)
            } else {
                console.error("Failed to fetch advice")
                setAdvice("The Sovereignty Agent is currently offline. Please try again later.")
            }
        } catch (e) {
            console.error("Error fetching advice", e)
            setAdvice("Error connecting to the Sovereignty Network.")
        }
    }

    const handleUnlock = async () => {
        if (!activeAccount) {
            setError("Please connect your wallet first.")
            return
        }

        setIsLoading(true)
        setError(null)

        let txId = ''

        try {
            // Construct transaction: Send 1 ALGO to self (as a test/burn/donation)
            // In production, this would be the app's treasury address
            const suggestedParams = await algodClient.getTransactionParams().do()

            const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
                sender: activeAccount.address,
                receiver: activeAccount.address, // Sending to self for safety in this demo
                amount: 1000000, // 1 ALGO
                suggestedParams,
                note: new TextEncoder().encode("Sovereignty Training Unlock"),
            })

            const encodedTxn = algosdk.encodeUnsignedTransaction(txn)

            // Sign transaction
            const signedTxns = await signTransactions([encodedTxn])

            // Filter out nulls
            const validSignedTxns = signedTxns.filter((stxn): stxn is Uint8Array => stxn !== null)

            if (validSignedTxns.length === 0) {
                throw new Error("Failed to sign transaction")
            }

            // Send transaction
            // Explicitly take the first transaction since we only created one
            const signedTxn = validSignedTxns[0]
            const response = await algodClient.sendRawTransaction(signedTxn).do()
            txId = response.txid
            console.log("Transaction sent with ID:", txId)

            // Wait for confirmation - increased to 20 rounds for reliability
            await algosdk.waitForConfirmation(algodClient, txId, 20)

            setIsUnlocked(true)

            // Fetch advice immediately after unlock
            console.log("Transaction confirmed. Fetching advice...")

            let currentAnalysis = analysis
            if (!currentAnalysis && activeAccount) {
                console.log("Analysis data missing, fetching now...")
                // We need to fetch it and wait
                try {
                    const res = await fetch(`http://localhost:8000/api/v1/analyze`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ address: activeAccount.address })
                    })
                    if (res.ok) {
                        currentAnalysis = await res.json()
                        setAnalysis(currentAnalysis)
                    }
                } catch (e) {
                    console.error("Failed to re-fetch analysis", e)
                }
            }

            if (currentAnalysis) {
                await fetchAdvice(currentAnalysis)
            } else {
                console.error("Cannot fetch advice: Analysis data still missing")
                setAdvice("Error: Could not retrieve portfolio data. Please refresh and try again.")
            }

        } catch (e: any) {
            console.error("Transaction failed", e)
            let errorMessage = e.message || "Transaction failed. Please try again."

            // Add TxID to error message if available
            if (txId) {
                errorMessage += ` (TxID: ${txId})`
                if (e.message && e.message.includes("not confirmed")) {
                    errorMessage = `Transaction sent (ID: ${txId}) but not confirmed in time. Please check your wallet or a block explorer.`
                }
            }

            setError(errorMessage)
            // Fallback alert to ensure user sees the error
            alert(errorMessage)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="container mx-auto px-4 py-12 max-w-4xl">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    Sovereignty Agent Training
                </h1>
                <p className="text-xl text-gray-400">
                    Get personalized, AI-driven advice to optimize your financial sovereignty.
                </p>
            </div>

            {!isUnlocked ? (
                <Card className="bg-slate-900/50 border-slate-800 max-w-md mx-auto">
                    <CardHeader className="text-center">
                        <div className="mx-auto bg-slate-800 p-4 rounded-full mb-4 w-16 h-16 flex items-center justify-center">
                            <Lock className="w-8 h-8 text-slate-400" />
                        </div>
                        <CardTitle className="text-2xl text-white">Unlock Training</CardTitle>
                        <CardDescription>
                            Access the Sovereignty Agent's analysis for 1 ALGO.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {error && (
                            <Alert variant="destructive" className="mb-4 bg-red-900/20 border-red-900">
                                <AlertTitle>Error</AlertTitle>
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        <Button
                            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-6 text-lg"
                            onClick={handleUnlock}
                            disabled={isLoading || !activeAccount}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Unlock className="mr-2 h-5 w-5" />
                                    Pay 1 ALGO to Unlock
                                </>
                            )}
                        </Button>
                        {!activeAccount && (
                            <p className="text-center text-sm text-yellow-500 mt-4">
                                Please connect your wallet to proceed.
                            </p>
                        )}
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-8 animate-in fade-in duration-500">
                    <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-center">
                        <p className="text-green-400 font-medium flex items-center justify-center gap-2">
                            <Unlock className="w-4 h-4" />
                            Training Unlocked
                        </p>
                    </div>

                    {advice ? (
                        <Card className="bg-slate-900/50 border-slate-800">
                            <CardHeader>
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="p-3 rounded-xl bg-purple-500/20 text-purple-400">
                                        <Brain className="w-8 h-8" />
                                    </div>
                                    <div>
                                        <CardTitle className="text-2xl text-white">Sovereignty Coach</CardTitle>
                                        <CardDescription>AI-Generated Analysis</CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="prose prose-invert max-w-none">
                                <ReactMarkdown>{advice}</ReactMarkdown>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="text-center py-12">
                            <Loader2 className="w-8 h-8 animate-spin mx-auto text-slate-500 mb-4" />
                            <p className="text-slate-400">Consulting the Sovereignty Network...</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
