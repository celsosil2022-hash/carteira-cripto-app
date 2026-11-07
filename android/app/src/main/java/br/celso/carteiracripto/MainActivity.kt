package br.celso.carteiracripto

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.webkit.*
import android.widget.ProgressBar
import androidx.appcompat.app.AppCompatActivity

/** App Carteira Cripto: abre a plataforma (Streamlit Cloud) em tela cheia, mantendo o login salvo. */
class MainActivity : AppCompatActivity() {
    private lateinit var web: WebView
    private lateinit var barra: ProgressBar
    private val inicio = "https://carteira-cripto-celso.streamlit.app/"
    // domínios que ficam dentro do app (o resto abre no navegador)
    private val internos = listOf("streamlit.app", "streamlit.io", "github.com", "githubusercontent.com", "snowflake.com")

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        web = findViewById(R.id.web)
        barra = findViewById(R.id.barra)

        CookieManager.getInstance().apply {
            setAcceptCookie(true)
            setAcceptThirdPartyCookies(web, true)
        }
        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = true
            setSupportMultipleWindows(false)
            javaScriptCanOpenWindowsAutomatically = true
            mediaPlaybackRequiresUserGesture = true
        }
        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, req: WebResourceRequest): Boolean {
                val host = req.url.host ?: return false
                if (internos.any { host == it || host.endsWith(".$it") }) return false
                startActivity(Intent(Intent.ACTION_VIEW, req.url))   // links externos (notícias) no navegador
                return true
            }
            override fun onPageStarted(view: WebView, url: String, favicon: Bitmap?) { barra.visibility = View.VISIBLE }
            override fun onPageFinished(view: WebView, url: String) {
                barra.visibility = View.GONE
                CookieManager.getInstance().flush()
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView, p: Int) { barra.progress = p }
        }
        if (savedInstanceState != null) web.restoreState(savedInstanceState) else web.loadUrl(inicio)
    }

    override fun onSaveInstanceState(out: Bundle) { super.onSaveInstanceState(out); web.saveState(out) }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else @Suppress("DEPRECATION") super.onBackPressed()
    }

    override fun onPause() { super.onPause(); CookieManager.getInstance().flush() }
}
