using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace aspnet_groupware.Pages;

public class IndexModel : PageModel
{
    private readonly ILogger<IndexModel> _logger;

    public IndexModel(ILogger<IndexModel> logger)
    {
        _logger = logger;
    }

    public void OnGet()
    {
        // 실제 로그인 정보 대신, 테스트용으로 "jh.bae" 값을 ViewData에 저장합니다.
        ViewData["userinfo"] = "jh.bae"; 
        
        // 실제 프로젝트에서는 인증된 사용자의 ID를 가져오는 코드가 들어갑니다.
        // 예: ViewData["userinfo"] = User.Identity.Name;
    }
}
