# AnimeVietsub cho Kodi — 0.1.0 (thử nghiệm)

Repository GitHub: https://github.com/sonle998/kodi-animevietsub

Địa chỉ nguồn Kodi / GitHub Pages: https://sonle998.github.io/kodi-animevietsub/

Gói repo trực tuyến: [repository.animevietsub-0.1.0.zip](https://sonle998.github.io/kodi-animevietsub/repository.animevietsub-0.1.0.zip)

Trong Kodi: File manager → Add source → nhập địa chỉ nguồn ở trên → Add-ons → Install from zip file → chọn repository ZIP → Install from repository → AnimeVietsub Repository → Video add-ons → AnimeVietsub.


Addon video Python 3 dành cho Kodi 19 trở lên. Đây là dự án cá nhân, không phải ứng dụng chính thức của Kodi hoặc AnimeVietsub. Không kèm phim, tài khoản hoặc khóa giải mã.

## Trạng thái thực tế

Đã viết addon, bộ phân tích trang, trình xử lý API nguồn trực tiếp, repo cục bộ tự chứa, công cụ dựng repo HTTP(S), workflow GitHub Pages và kiểm tra tự động. Chưa thử chạy trong ứng dụng Kodi thực tế. Môi trường trước đó bị website yêu cầu xác minh người dùng Việt Nam; chưa xác minh một phiên xem thành công trực tiếp trên AnimeVietsub.

**Không đảm bảo phát được mọi tập hoặc máy chủ.** Nguồn mã hóa riêng, player chỉ chạy bằng JavaScript, CAPTCHA/xác minh, DRM chưa được hỗ trợ. Addon báo rõ thay vì giao token mã hóa cho Kodi như URL phim. Để hoàn thiện máy chủ chưa hỗ trợ cần link phim/tập và phản hồi nguồn hợp lệ từ phiên truy cập của người dùng; không cần gửi mật khẩu/cookie.

## Tính năng

- Menu Mới cập nhật, tìm kiếm, thể loại/danh mục thực tế của trang.
- Poster, giới thiệu, nút xem và danh sách tập/máy chủ.
- Giao diện danh sách chuẩn Kodi, điều khiển bằng remote.
- HTTP cookie jar riêng của addon; timeout và tên miền cấu hình được.
- Link dự phòng https://bit.ly/animevietsubtv được dùng khi người dùng chọn cập nhật tên miền.
- Chỉ đọc HTML/API; không thực thi JS quảng cáo của trang. Không tải hàng loạt script/iframe trang trí.
- Resolver nhận HLS/MP4/WebM/DASH trực tiếp, source declaration đơn giản và iframe có nguồn trực tiếp. DASH cần InputStream Adaptive đã cài từ kho Kodi.
- Không tự vượt xác minh, không giả kết quả đã xem quảng cáo, không chạy JS mã hóa hoặc giải DRM.

## Cài nhanh bằng ZIP addon

1. Trên Kodi: Settings → System → Add-ons → Unknown sources, bật để cho phép addon cá nhân.
2. Add-ons → Install from zip file → chọn `plugin.video.animevietsub-0.1.0.zip`.
3. Mở Video add-ons → AnimeVietsub.
4. Nếu tên miền thay đổi, mở Cài đặt hoặc chọn cập nhật tên miền qua link dự phòng.

## Repository cục bộ tự chứa

Chọn `repository.animevietsub-0.1.0-local.zip` trong Install from zip file, sau đó Install from repository → AnimeVietsub Repository → Video add-ons → AnimeVietsub.

Repo này dùng các đường dẫn `special://home/addons/repository.animevietsub/repo/` và chứa sẵn addon ZIP, chỉ mục và checksum. Nó không cần hosting để đọc chỉ mục. Cách dùng đường dẫn dựa trên VFS của Kodi; chưa thử trên Kodi thật. Nếu bản Kodi không đọc repo cục bộ, dùng ZIP addon trực tiếp phía trên.

Repo cục bộ không tự lấy các phiên bản mới từ Internet. Khi có bản mới, cài ZIP repo mới. Kết nối Internet vẫn cần để đọc/phát nội dung AnimeVietsub.

## Repository trực tuyến / GitHub Pages

Từ thư mục dự án, chạy:

```bash
python tools/build_repo.py --base-url https://DIA_CHI_THUC_CUA_BAN/ --output public-dist
```

Đây là tham số bạn cần thay bằng hosting thật; không có URL giả nằm trong ZIP repo cục bộ. Upload toàn bộ `public-dist/site/` lên đúng URL đó; cài ZIP repository vừa tạo. Feed có `addons.xml`, checksum, từng ZIP theo đúng addon id/version và SHA-256.

GitHub Pages xuất bản từ nhánh `main`, thư mục `/docs`. Repo online đã chuẩn bị đúng địa chỉ trong các ZIP. Để cập nhật addon: sửa version trong addon.xml và VERSION của tools/build_repo.py, chạy kiểm tra, chạy `python tools/publish_files.py`, rồi commit/push mã và docs/. Kodi đọc chỉ mục mới khi kiểm tra cập nhật. Không dùng workflow GitHub Actions riêng cho bước dựng; GitHub Pages tự triển khai các file docs/ đã commit.

## Dùng repo trong mạng LAN

Cài Python 3 trên máy tính và chạy:

```bash
python tools/serve_repo.py
```

Máy tính in ra địa chỉ IP LAN và cổng 8765. Trong File manager của Kodi, Add source địa chỉ được in, rồi Install from zip file chọn nguồn đó. Máy tính cần bật, cùng mạng với TV và cho phép kết nối cổng đã chọn. Chỉ dùng trong mạng tin cậy. HTTP LAN không cung cấp cập nhật công khai hay mã hóa truyền tải. Có thể chỉ định IP với `--ip` và cổng với `--port`.

## Phát triển / xác minh

```bash
python -m unittest discover -s tests -v
python tools/build_repo.py
```

Kiểm tra gồm cấu trúc XML/ZIP/checksum, menu Kodi mô phỏng, danh sách/tập, nguồn trực tiếp, giữ nguyên token cho API, loại URL quảng cáo và không coi token mã hóa là nguồn phát. Mô phỏng không thay thế kiểm tra phát phim trên Kodi thật.

Bộ phân tích dùng cấu trúc công khai `.TPostMv`, `.Title`, `.watch_button_more`, `#list-server` và các thuộc tính data-id/data-play/data-hash. API được tham khảo từ source công khai của dự án anime-vsub/desktop-web, không sao chép thư viện giải mã hoặc mã triển khai từ dự án đó.

Nguồn tham khảo:
- https://kodi.wiki/view/Addon.xml
- https://kodi.wiki/view/Add-on_repositories
- https://kodi.wiki/view/Python_libraries
- https://github.com/xbmc/xbmc/blob/master/xbmc/addons/Repository.cpp
- https://github.com/anime-vsub/desktop-web

Mã nguồn mới: GPL-3.0-only; xem LICENSE. Logo do người dùng cung cấp, không cấp thêm quyền với thương hiệu của bên thứ ba.
