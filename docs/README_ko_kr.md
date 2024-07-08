# github-release-monitor
[![Stacks](https://skillicons.dev/icons?i=html,css,js,githubactions,python)](https://skillicons.dev)

## 사전 환경설정
**1. 먼저, 리포지토리를 `fork` 해주세요.**
<br>

**2. 깃허브 설정으로 가서 토큰을 발급 받아주세요.**
- 토큰에는 `repo`와 `workflow` 권한이 활성화 되어있어야 합니다.
<br>

**3. 포크한 리포지토리에 토큰을 입력해주세요.**
- 토큰 이름의 경우 별도의 소스코드 수정을 하시지 않는 한 `YOUR_GITHUB_TOKEN`으로 써주세요.
<br>

**4. Actions 탭으로 가서 액션을 최초 1회 실행 해주세요.**

![screenshot.png](img/screenshot.png)

- 만약 Actions를 실행 시 권한 관련 오류가 발생했다면, 설정에서 액션에 `읽기 및 쓰기`권한으로 바꿔주세요.
- 조직 레포의 경우 조직 설정에 의해 막혀있을수도 있습니다.
<br>

## 사용 방법
**1. `settings.json`을 수정해주세요.**
```
{
    "repository_link" : [
        "https://github.com/karpitony/github-release-monitor",
        "https://github.com/karpitony/eft-where-am-i"
    ]
}
```
위 예시와 같이 리포지토리 링크를 **문자열 형태**로 넣어주시고, **쉼표로 구분** 해주세요.
