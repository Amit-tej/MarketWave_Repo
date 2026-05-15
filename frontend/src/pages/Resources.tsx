import React, {useState} from 'react'

function AccordionItem({q, a, i}:{q:string, a:string, i: number}){
  const [open, setOpen] = useState(false)
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-3 cursor-pointer hover:shadow-md transition-shadow duration-200">
      <div
        onClick={()=> setOpen(!open)}
        className="flex justify-between items-center p-4 font-semibold text-gray-900"
      >
        <span>{q}</span>
        <span className="text-xl text-gray-500">{open ? '−' : '+'}</span>
      </div>
      {open && <div className="px-4 pb-4 pt-2 border-t border-gray-100 text-gray-600 leading-relaxed">{a}</div>}
    </div>
  )
}

export default function Resources(){
  const faqs = [
    {
      q: 'What is Modal Price?',
      a: 'Modal price is the price that occurs most frequently in the market during a given day or time period. It represents the typical transaction price and is used in agricultural markets to indicate prevailing prices.'
    },
    {
      q: 'How do price predictions work?',
      a: 'Our system uses ensemble machine learning models (XGBoost, Prophet, LSTM) that analyze historical price patterns, seasonal trends, and market data to forecast future prices up to 30 days in advance.'
    },
    {
      q: 'What is explainability and why does it matter?',
      a: 'Explainability shows which factors (features) most influence the predicted prices. This helps you understand the reasoning behind predictions and make informed farming decisions.'
    },
    {
      q: 'How accurate are the predictions?',
      a: 'Accuracy varies by commodity and market conditions. Our models achieve 75-85% accuracy for 7-day predictions. Always cross-reference with other sources for critical decisions.'
    },
    {
      q: 'How often is data updated?',
      a: 'Historical price data is updated daily from various agricultural markets. Live market data may have a 24-hour lag depending on official data releases.'
    },
    {
      q: 'How can I use this for better returns?',
      a: 'Use the price predictions to time your harvest and sales. Compare prices across markets to find the best selling locations. Monitor volatility trends to plan your crop selection.'
    },
    {
      q: 'Is my data private?',
      a: 'Yes. Agricultural Intelligence is a public forecasting tool. Your selections and queries are not stored or tracked. All data comes from public agricultural market data sources.'
    },
    {
      q: 'What commodities are covered?',
      a: 'We currently cover: Brinjal, Green Chilli, Onion, Potato, and Tomato. More commodities will be added as we expand market coverage.'
    }
  ]

  const resources = [
    {title: 'AgMarketNet', url: 'https://agmarknet.gov.in', desc: 'Official daily commodity prices from NCDEX and APEDA'},
    {title: 'Data.gov.in', url: 'https://data.gov.in', desc: 'Open government data portal'},
    {title: 'Ministry of Agriculture', url: 'https://agriculture.gov.in', desc: 'Government agriculture policies and information'},
  ]

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center">
          Resources
        </h1>
        <p className="text-lg text-gray-600">Educational resources and guides for farmers</p>
      </div>

      {/* About Section */}
      <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-xl border border-blue-200 p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">About Agricultural Intelligence</h2>
        <p className="text-gray-700 text-lg leading-relaxed mb-8">
          <span className="text-black">Agricultural Intelligence</span> is an AI-powered agricultural intelligence platform that helps farmers make informed decisions about when and where to sell their crops.
          By providing accurate price predictions and market comparisons, we aim to increase farmer incomes and reduce market uncertainty.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-6 text-center shadow-sm border border-gray-100">
            <div className="text-4xl mb-3">📈</div>
            <div className="font-semibold text-gray-900 mb-1">Real Data</div>
            <div className="text-sm text-gray-600">From official markets</div>
          </div>
          <div className="bg-white rounded-lg p-6 text-center shadow-sm border border-gray-100">
            <div className="text-4xl mb-3">🤖</div>
            <div className="font-semibold text-gray-900 mb-1">AI Powered</div>
            <div className="text-sm text-gray-600">Machine learning models</div>
          </div>
          <div className="bg-white rounded-lg p-6 text-center shadow-sm border border-gray-100">
            <div className="text-4xl mb-3">🌾</div>
            <div className="font-semibold text-gray-900 mb-1">Farmer First</div>
            <div className="text-sm text-gray-600">Designed for farmers</div>
          </div>
        </div>
      </div>

      {/* FAQs */}
      <div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
          <span className="mr-2">❓</span> Frequently Asked Questions
        </h2>
        {faqs.map((item, i)=> <AccordionItem key={i} q={item.q} a={item.a} i={i} />)}
      </div>

      {/* Google Search Integration */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <span className="mr-2">🔍</span> Search Latest Market Information
        </h2>
        <div className="mb-4">
          <div className="gcse-search"></div>
        </div>
        <p className="text-sm text-gray-600">
          Use Google search to find the latest commodity prices, market news, and agricultural information from reliable sources.
        </p>
      </div>

      {/* External Resources */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <span className="mr-2">🔗</span> External Resources
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {resources.map((res, i) => (
            <a
              key={i}
              href={res.url}
              target="_blank"
              rel="noreferrer"
              className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-decoration-none text-inherit hover:bg-blue-100 transition-colors duration-200 block"
            >
              <div className="font-semibold text-blue-700 mb-2 flex items-center">
                <span className="mr-2">🔗</span> {res.title}
              </div>
              <div className="text-sm text-gray-600">{res.desc}</div>
            </a>
          ))}
        </div>
      </div>

      {/* Contact Section */}
      <div className="bg-green-50 rounded-xl border border-green-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
          <span className="mr-2">📧</span> Get Help
        </h3>
        <p className="text-gray-700 mb-4">Have questions or feedback? We'd love to hear from you!</p>
        <button className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors duration-200">
          Contact Support
        </button>
      </div>
    </div>
  )
}
