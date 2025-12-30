'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Server,
  Shield,
  Coins,
  Award,
  Lock,
  Cpu,
  HardDrive,
  Wifi,
  Clock,
  DollarSign,
  Cloud,
  Terminal,
  Monitor,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Copy,
  Check,
  AlertTriangle,
  Zap,
  Globe,
  Heart
} from 'lucide-react'

// Code block component with copy functionality
function CodeBlock({ children, title }: { children: string; title?: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(children)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group">
      {title && (
        <div className="text-xs text-slate-400 mb-1 font-medium">{title}</div>
      )}
      <pre className="bg-slate-950 border border-slate-800 rounded-lg p-4 overflow-x-auto text-sm">
        <code className="text-cyan-400">{children}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-2 bg-slate-800 hover:bg-slate-700 rounded opacity-0 group-hover:opacity-100 transition-opacity"
        title="Copy to clipboard"
      >
        {copied ? (
          <Check className="w-4 h-4 text-green-400" />
        ) : (
          <Copy className="w-4 h-4 text-slate-400" />
        )}
      </button>
    </div>
  )
}

// FAQ Item component
function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="border-b border-slate-800 last:border-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-4 text-left hover:text-orange-400 transition-colors"
      >
        <span className="font-medium text-slate-200">{question}</span>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-5 h-5 text-slate-400 flex-shrink-0" />
        )}
      </button>
      {isOpen && (
        <div className="pb-4 text-slate-400 text-sm leading-relaxed">
          {answer}
        </div>
      )}
    </div>
  )
}

// Tab button component
function TabButton({
  active,
  onClick,
  children,
  icon: Icon
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
  icon: React.ElementType
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
        active
          ? 'bg-orange-600 text-white'
          : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
      }`}
    >
      <Icon className="w-4 h-4" />
      {children}
    </button>
  )
}

export default function RunANodePage() {
  const [activeTab, setActiveTab] = useState<'nodekit' | 'linux' | 'wsl' | 'cloud'>('nodekit')

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      {/* ============ HERO SECTION ============ */}
      <section className="text-center space-y-6 py-8">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-orange-500/10 border border-orange-500/30 rounded-full text-orange-400 text-sm">
          <Server className="w-4 h-4" />
          Contribute to Decentralization
        </div>

        <h1 className="text-4xl md:text-5xl font-bold">
          Run Your Own
          <span className="text-orange-400"> Algorand Node</span>
        </h1>

        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          Contribute to decentralization, earn rewards, achieve sovereignty
        </p>

        {/* Key Stats */}
        <div className="flex flex-wrap justify-center gap-6 pt-4">
          <div className="flex items-center gap-2 text-slate-300">
            <DollarSign className="w-5 h-5 text-green-400" />
            <span className="font-medium">~$20/month</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <Clock className="w-5 h-5 text-cyan-400" />
            <span className="font-medium">2 hours setup</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <Coins className="w-5 h-5 text-yellow-400" />
            <span className="font-medium">24/7 passive income</span>
          </div>
        </div>

        <div className="flex flex-wrap justify-center gap-4 pt-4">
          <a
            href="#setup"
            className="inline-flex items-center gap-2 px-6 py-3 bg-orange-600 hover:bg-orange-500 rounded-lg text-white font-medium transition-colors"
          >
            Get Started
            <ChevronDown className="w-4 h-4" />
          </a>
          <a
            href="https://developer.algorand.org/docs/run-a-node/participate/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-200 font-medium transition-colors"
          >
            Official Docs
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </section>

      {/* ============ WHY RUN A NODE ============ */}
      <section id="why" className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span className="text-orange-400">1.</span> Why Run a Node?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Secure the Network */}
          <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/30">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
                  <Shield className="w-6 h-6 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-cyan-400">Secure the Network</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Your node validates transactions and votes on blocks.
                    More nodes = more decentralized = more secure.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Earn Staking Rewards */}
          <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0">
                  <Coins className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-green-400">Earn Staking Rewards</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    30,000+ ALGO stake earns protocol rewards.
                    Rewards paid automatically for valid block proposals.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* True Sovereignty */}
          <Card className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border-orange-500/30">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0">
                  <Lock className="w-6 h-6 text-orange-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-orange-400">True Sovereignty</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Verify transactions yourself. Don&apos;t trust third parties.
                    Be part of the solution, not the problem.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ============ REQUIREMENTS ============ */}
      <section id="requirements" className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span className="text-orange-400">2.</span> Requirements
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Hardware Requirements */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Cpu className="w-5 h-5 text-cyan-400" />
                Hardware Requirements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-2 text-slate-400 font-medium">Component</th>
                      <th className="text-left py-2 text-slate-400 font-medium">Minimum</th>
                      <th className="text-left py-2 text-slate-400 font-medium">Recommended</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-300">
                    <tr className="border-b border-slate-800">
                      <td className="py-2 flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-slate-500" /> CPU
                      </td>
                      <td className="py-2">4 cores</td>
                      <td className="py-2 text-green-400">8+ cores</td>
                    </tr>
                    <tr className="border-b border-slate-800">
                      <td className="py-2 flex items-center gap-2">
                        <Zap className="w-4 h-4 text-slate-500" /> RAM
                      </td>
                      <td className="py-2">8 GB</td>
                      <td className="py-2 text-green-400">16 GB</td>
                    </tr>
                    <tr className="border-b border-slate-800">
                      <td className="py-2 flex items-center gap-2">
                        <HardDrive className="w-4 h-4 text-slate-500" /> Storage
                      </td>
                      <td className="py-2">100 GB SSD</td>
                      <td className="py-2 text-green-400">256 GB NVMe</td>
                    </tr>
                    <tr className="border-b border-slate-800">
                      <td className="py-2 flex items-center gap-2">
                        <Wifi className="w-4 h-4 text-slate-500" /> Network
                      </td>
                      <td className="py-2">10 Mbps</td>
                      <td className="py-2 text-green-400">100 Mbps+</td>
                    </tr>
                    <tr>
                      <td className="py-2 flex items-center gap-2">
                        <Clock className="w-4 h-4 text-slate-500" /> Uptime
                      </td>
                      <td className="py-2">95%+</td>
                      <td className="py-2 text-green-400">99%+</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Cost Estimates */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <DollarSign className="w-5 h-5 text-green-400" />
                Cost Estimates
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Cloud className="w-4 h-4 text-cyan-400" />
                    <span className="text-slate-300">Cloud VPS</span>
                  </div>
                  <span className="text-slate-400">$20-50/month</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Server className="w-4 h-4 text-purple-400" />
                    <span className="text-slate-300">Home Server</span>
                  </div>
                  <span className="text-slate-400">$150-300 one-time</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-400" />
                    <span className="text-slate-300">Electricity (home)</span>
                  </div>
                  <span className="text-slate-400">~$5-10/month</span>
                </div>
              </div>

              <div className="bg-slate-800/50 rounded-lg p-3 text-sm">
                <div className="text-slate-400 mb-2">
                  <strong className="text-slate-200">Stake Requirements:</strong>
                </div>
                <ul className="space-y-1 text-slate-400">
                  <li>• Minimum to run: <span className="text-green-400">0.1 ALGO</span></li>
                  <li>• Minimum for rewards: <span className="text-yellow-400">30,000 ALGO</span></li>
                  <li>• No maximum stake limit</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4 text-sm">
          <p className="text-slate-300">
            <span className="text-cyan-400 font-medium">Note:</span> You can run a node with any amount, but staking rewards require 30k+ ALGO.
            Even small participants strengthen decentralization!
          </p>
        </div>
      </section>

      {/* ============ REWARDS & INCENTIVES ============ */}
      <section id="rewards" className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span className="text-orange-400">3.</span> Rewards & Incentives
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Coins className="w-5 h-5 text-green-400" />
                Protocol Rewards
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-400">
              <ul className="space-y-2">
                <li>• Block proposers earn transaction fees</li>
                <li>• Stakers with 30k+ ALGO receive ongoing rewards</li>
                <li>• Rewards distributed automatically - no claiming needed</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Globe className="w-5 h-5 text-purple-400" />
                Governance
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-400">
              <ul className="space-y-2">
                <li>• Node runners can participate in Algorand governance</li>
                <li>• Vote on protocol upgrades</li>
                <li>• Influence fund allocation</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ============ SETUP OPTIONS ============ */}
      <section id="setup" className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span className="text-orange-400">4.</span> Setup Options
        </h2>

        {/* Tab Buttons */}
        <div className="flex flex-wrap gap-2">
          <TabButton
            active={activeTab === 'nodekit'}
            onClick={() => setActiveTab('nodekit')}
            icon={Zap}
          >
            NodeKit (Easiest)
          </TabButton>
          <TabButton
            active={activeTab === 'linux'}
            onClick={() => setActiveTab('linux')}
            icon={Terminal}
          >
            Manual Linux
          </TabButton>
          <TabButton
            active={activeTab === 'wsl'}
            onClick={() => setActiveTab('wsl')}
            icon={Monitor}
          >
            Windows (WSL)
          </TabButton>
          <TabButton
            active={activeTab === 'cloud'}
            onClick={() => setActiveTab('cloud')}
            icon={Cloud}
          >
            Cloud Providers
          </TabButton>
        </div>

        {/* Tab Content */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardContent className="pt-6">
            {/* NodeKit Tab */}
            {activeTab === 'nodekit' && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-green-400 font-medium">
                  <CheckCircle2 className="w-5 h-5" />
                  Recommended for Beginners
                </div>

                <p className="text-slate-400">
                  NodeKit is a terminal-based installer from the Algorand Foundation that handles
                  all the complexity for you. Works on Linux and Mac.
                </p>

                <div className="space-y-4">
                  <CodeBlock title="Install NodeKit">
                    {`curl -fsSL https://nodekit.run/install.sh | bash`}
                  </CodeBlock>

                  <CodeBlock title="Start a participation node">
                    {`nodekit start`}
                  </CodeBlock>
                </div>

                <div className="flex flex-wrap gap-4 pt-4">
                  <a
                    href="https://github.com/algorandfoundation/nodekit"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300"
                  >
                    <ExternalLink className="w-4 h-4" />
                    NodeKit GitHub
                  </a>
                  <a
                    href="https://nodekit.run"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300"
                  >
                    <ExternalLink className="w-4 h-4" />
                    nodekit.run
                  </a>
                </div>
              </div>
            )}

            {/* Linux Tab */}
            {activeTab === 'linux' && (
              <div className="space-y-4">
                <p className="text-slate-400">
                  Manual installation gives you full control over your node setup.
                  Recommended for experienced Linux users.
                </p>

                <div className="space-y-4">
                  <CodeBlock title="1. Update system">
                    {`sudo apt update && sudo apt upgrade -y`}
                  </CodeBlock>

                  <CodeBlock title="2. Add Algorand repository">
                    {`curl -o - https://releases.algorand.com/key.pub | sudo tee /etc/apt/trusted.gpg.d/algorand.asc
sudo add-apt-repository "deb [arch=amd64] https://releases.algorand.com/deb/ stable main"`}
                  </CodeBlock>

                  <CodeBlock title="3. Install algorand">
                    {`sudo apt update && sudo apt install -y algorand`}
                  </CodeBlock>

                  <CodeBlock title="4. Start the node">
                    {`sudo systemctl start algorand
sudo systemctl enable algorand`}
                  </CodeBlock>

                  <CodeBlock title="5. Check status">
                    {`goal node status -d /var/lib/algorand`}
                  </CodeBlock>
                </div>

                <a
                  href="https://developer.algorand.org/docs/run-a-node/setup/install/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 pt-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  Full installation guide
                </a>
              </div>
            )}

            {/* WSL Tab */}
            {activeTab === 'wsl' && (
              <div className="space-y-4">
                <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-3 text-sm">
                  <p className="text-orange-400 font-medium">
                    This is how the Sovereignty Analyzer creator runs his node!
                  </p>
                </div>

                <p className="text-slate-400">
                  Windows Subsystem for Linux (WSL) lets you run a full Linux environment on Windows.
                  Perfect for Windows users who want to participate.
                </p>

                <div className="space-y-4">
                  <div className="text-sm text-slate-300 font-medium">1. Enable WSL2 on Windows</div>
                  <CodeBlock>
                    {`# Run in PowerShell as Administrator
wsl --install`}
                  </CodeBlock>

                  <div className="text-sm text-slate-300 font-medium">2. Install Ubuntu from Microsoft Store</div>
                  <p className="text-sm text-slate-500">
                    Search for &quot;Ubuntu&quot; in the Microsoft Store and install the latest LTS version.
                  </p>

                  <div className="text-sm text-slate-300 font-medium">3. Follow Linux installation steps</div>
                  <p className="text-sm text-slate-500">
                    Once Ubuntu is running, follow the Manual Linux instructions above.
                  </p>

                  <div className="text-sm text-slate-300 font-medium">4. Configure to run at startup (optional)</div>
                  <CodeBlock>
                    {`# Add to Windows Task Scheduler to auto-start WSL
wsl -d Ubuntu -u root -- service algorand start`}
                  </CodeBlock>
                </div>
              </div>
            )}

            {/* Cloud Tab */}
            {activeTab === 'cloud' && (
              <div className="space-y-4">
                <p className="text-slate-400">
                  Cloud VPS providers offer reliable hosting with guaranteed uptime.
                  Choose a provider that aligns with your decentralization values.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="font-medium text-green-400 mb-2">Hetzner (Cheapest)</div>
                    <div className="text-sm text-slate-400 space-y-1">
                      <div>~€5-10/month</div>
                      <div>Europe-based, good privacy</div>
                      <div className="text-green-400">Recommended for sovereignty</div>
                    </div>
                    <a
                      href="https://www.hetzner.com/cloud"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 mt-2"
                    >
                      hetzner.com <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="font-medium text-cyan-400 mb-2">DigitalOcean</div>
                    <div className="text-sm text-slate-400 space-y-1">
                      <div>~$20-40/month</div>
                      <div>Easy setup, good docs</div>
                      <div>Great for beginners</div>
                    </div>
                    <a
                      href="https://www.digitalocean.com/products/droplets"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 mt-2"
                    >
                      digitalocean.com <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <div className="font-medium text-purple-400 mb-2">Vultr</div>
                    <div className="text-sm text-slate-400 space-y-1">
                      <div>~$20-40/month</div>
                      <div>Global locations</div>
                      <div>Good performance</div>
                    </div>
                    <a
                      href="https://www.vultr.com/products/cloud-compute/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 mt-2"
                    >
                      vultr.com <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg p-4 border border-red-500/30">
                    <div className="font-medium text-red-400 mb-2">AWS/GCP/Azure</div>
                    <div className="text-sm text-slate-400 space-y-1">
                      <div>Various pricing</div>
                      <div className="text-red-400">Hyperscale cloud - less sovereign</div>
                      <div>Works, but not recommended</div>
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-sm">
                  <p className="text-yellow-400">
                    <strong>Pro tip:</strong> Choose independent data center providers (Hetzner, OVH, Vultr)
                    over hyperscale cloud (AWS, Google, Azure) for better decentralization.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* ============ KEY REGISTRATION ============ */}
      <section id="registration" className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span className="text-orange-400">5.</span> Key Registration
        </h2>

        <p className="text-slate-400">
          After your node is synced, you need to register participation keys to start
          validating blocks and earning rewards.
        </p>

        <div className="space-y-4">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center flex-shrink-0 text-orange-400 font-bold">
                  1
                </div>
                <div>
                  <h4 className="font-medium text-slate-200">Generate participation keys</h4>
                  <p className="text-sm text-slate-400 mt-1">
                    Keys are generated on your node and never leave it.
                  </p>
                  <CodeBlock>
                    {`goal account addpartkey -a YOUR_ADDRESS --roundFirstValid ROUND --roundLastValid ROUND+3000000`}
                  </CodeBlock>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center flex-shrink-0 text-orange-400 font-bold">
                  2
                </div>
                <div>
                  <h4 className="font-medium text-slate-200">Sign key registration transaction</h4>
                  <p className="text-sm text-slate-400 mt-1">
                    You can use web-based tools or your wallet to sign the keyreg transaction.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center flex-shrink-0 text-orange-400 font-bold">
                  3
                </div>
                <div>
                  <h4 className="font-medium text-slate-200">Wait for registration to take effect</h4>
                  <p className="text-sm text-slate-400 mt-1">
                    Registration takes approximately 320 rounds (~16 minutes) to become active.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-4">
            <a
              href="https://algotools.org"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-200 transition-colors"
            >
              <Globe className="w-4 h-4 text-cyan-400" />
              AlgoTools.org
              <ExternalLink className="w-4 h-4 text-slate-500" />
            </a>
            <a
              href="https://nodely.io/blog/algorand-key-reg/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-200 transition-colors"
            >
              <Server className="w-4 h-4 text-cyan-400" />
              Nodely Key Registration Guide
              <ExternalLink className="w-4 h-4 text-slate-500" />
            </a>
          </div>
        </div>
      </section>

      {/* ============ MONITORING ============ */}
      <section id="monitoring" className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span className="text-orange-400">6.</span> Monitoring
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Terminal className="w-5 h-5 text-cyan-400" />
                Built-in Commands
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <CodeBlock title="Check node status">
                {`goal node status`}
              </CodeBlock>
              <CodeBlock title="List participation keys">
                {`goal account listpartkeys`}
              </CodeBlock>
              <CodeBlock title="Check account info">
                {`goal account dump -a YOUR_ADDRESS`}
              </CodeBlock>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Monitor className="w-5 h-5 text-purple-400" />
                External Tools
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-200 text-sm">Nodely Telemetry</h4>
                <p className="text-xs text-slate-400 mt-1">Free monitoring service for your node</p>
                <a
                  href="https://nodely.io"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 mt-1"
                >
                  nodely.io <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              <div>
                <h4 className="font-medium text-slate-200 text-sm">Allo Alerts</h4>
                <p className="text-xs text-slate-400 mt-1">Participation key expiry notifications</p>
                <a
                  href="https://allo.info"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 mt-1"
                >
                  allo.info <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              <div className="bg-slate-800/50 rounded-lg p-3 text-xs text-slate-400">
                <strong className="text-slate-300">What to Monitor:</strong>
                <ul className="mt-2 space-y-1">
                  <li>• Node sync status</li>
                  <li>• Participation key expiry</li>
                  <li>• Block proposals (occasional is normal)</li>
                  <li>• Network connectivity</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ============ FAQ ============ */}
      <section id="faq" className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span className="text-orange-400">7.</span> Frequently Asked Questions
        </h2>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardContent className="pt-6">
            <FAQItem
              question="How much ALGO do I need to start?"
              answer="Any amount works for running a node, but 30,000+ ALGO is required to receive protocol staking rewards. Even with less, you're still contributing to decentralization."
            />
            <FAQItem
              question="Will I lose my ALGO if my node goes offline?"
              answer="No. Your ALGO is never locked or at risk. If your node goes offline, you simply miss out on potential rewards during that time. There's no slashing or penalties on Algorand."
            />
            <FAQItem
              question="Can I run multiple accounts on one node?"
              answer="Yes, but limit to 4 accounts maximum. More accounts cause performance issues and increase the chances of missing blocks. Each account needs its own participation keys."
            />
            <FAQItem
              question="How long until I see rewards?"
              answer="This depends on your stake size. Larger stakes = more frequent block proposals = more frequent rewards. With 30k ALGO, you might propose a block every few days. With 1M ALGO, potentially multiple times per day."
            />
            <FAQItem
              question="Is it worth it for small holders?"
              answer="Yes! Even without protocol rewards (under 30k ALGO), you're strengthening decentralization and gaining valuable experience running infrastructure. Every node matters."
            />
            <FAQItem
              question="How often do I need to renew my participation keys?"
              answer="Keys are generated for a specific round range (typically 3 million rounds, ~3 months). You should renew them before they expire. Tools like Allo can alert you when renewal is needed."
            />
            <FAQItem
              question="Can I run a node on a Raspberry Pi?"
              answer="Yes! A Raspberry Pi 5 with 8GB RAM and a fast SSD works well for participation nodes. It's an excellent choice for home node runners focused on sovereignty."
            />
          </CardContent>
        </Card>
      </section>

      {/* ============ FOOTER CTAs ============ */}
      <section className="space-y-6 pb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/analyze"
            className="flex items-center gap-3 p-4 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/30 rounded-lg transition-colors group"
          >
            <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
              <Shield className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <div className="font-medium text-orange-400 group-hover:text-orange-300">
                Check Your Status
              </div>
              <div className="text-xs text-slate-400">
                See if you&apos;re participating
              </div>
            </div>
          </Link>

          <Link
            href="/network"
            className="flex items-center gap-3 p-4 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded-lg transition-colors group"
          >
            <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
              <Globe className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <div className="font-medium text-cyan-400 group-hover:text-cyan-300">
                Network Statistics
              </div>
              <div className="text-xs text-slate-400">
                View decentralization metrics
              </div>
            </div>
          </Link>

          <a
            href="https://discord.gg/algorand"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-4 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-lg transition-colors group"
          >
            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <Heart className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <div className="font-medium text-purple-400 group-hover:text-purple-300">
                Join the Community
              </div>
              <div className="text-xs text-slate-400">
                Discord #node-runners
              </div>
            </div>
            <ExternalLink className="w-4 h-4 text-slate-500 ml-auto" />
          </a>
        </div>

        <div className="text-center text-sm text-slate-500 pt-4">
          <p>
            Questions? Join the{' '}
            <a
              href="https://discord.gg/algorand"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300"
            >
              Algorand Discord
            </a>{' '}
            or check the{' '}
            <a
              href="https://developer.algorand.org/docs/run-a-node/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300"
            >
              official documentation
            </a>
            .
          </p>
        </div>
      </section>
    </div>
  )
}
